import os
import pickle
import time
from multiprocessing import Pipe

import numpy as np

import matisse_controller.config as cfg
from matisse_controller.shamrock_ple.ccd import CCD
from matisse_controller.shamrock_ple.plotting import *
from matisse_controller.shamrock_ple.shamrock import Shamrock

ccd: CCD = None
shamrock: Shamrock = None


class PLE:
    """PLE scanning functionality with the Andor Shamrock and Newton CCD."""

    def __init__(self, matisse):
        self.matisse = matisse
        self.ple_exit_flag = False
        self.analysis_plot_processes = []
        self.spectrum_plot_processes = []

    @staticmethod
    def load_andor_libs():
        """
        Initialize the interfaces to the Andor Shamrock and Newton CCD. This only needs to be run once, since the two
        devices are global variables.
        """
        global ccd
        global shamrock
        if ccd is None:
            ccd = CCD()
            print('CCD initialized.')
        if shamrock is None:
            shamrock = Shamrock()
            print('Shamrock initialized.')

    @staticmethod
    def clean_up_globals():
        """
        Remove references to the Shamrock and Newton, allowing us to re-initialize them again later.
        """
        global ccd
        global shamrock
        ccd = None
        shamrock = None

    def start_ple_scan(self, scan_name: str, scan_location: str, initial_wavelength: float, final_wavelength: float,
                       step: float, center_wavelength: float, grating_grooves: int, *ccd_args, **ccd_kwargs):
        """
        Perform a PLE scan using the Andor Shamrock spectrometer and Newton CCD.

        Generates text files with data from each spectrum taken during the scan, and pickles the Python dictionary of
        all data into {name}.pickle.

        Parameters
        ----------
        scan_name
            a unique name to give the PLE measurement, which will be included in the name of all the data files
        scan_location
            the name of a folder to contain all relevant scan data
        initial_wavelength
            starting wavelength for the PLE scan
        final_wavelength
            ending wavelength for the PLE scan
        step
            the desired change in wavelength between each individual scan
        center_wavelength
            the wavelength at which to set the spectrometer
        grating_grooves
            the number of grooves to use for the spectrometer grating
        *ccd_args
            args to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        **ccd_kwargs
            kwargs to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        """
        self.ple_exit_flag = False

        if not scan_name:
            print('WARNING: Name of PLE scan is required.')
            return
        if not scan_location:
            print('WARNING: Location of PLE scan is required.')
            return

        data_file_name = os.path.join(scan_location, f"{scan_name}.pickle")

        if os.path.exists(data_file_name):
            print(f"WARNING: A PLE scan has already been run for '{scan_name}'. Choose a new name and try again.")
            return

        PLE.load_andor_libs()
        print(f"Setting spectrometer grating to {grating_grooves} grvs and center wavelength to {center_wavelength}...")
        shamrock.set_grating_grooves(grating_grooves)
        shamrock.set_center_wavelength(center_wavelength)
        if self.ple_exit_flag:
            return
        ccd.setup(*ccd_args, **ccd_kwargs)
        wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
        wavelength_range = abs(round(final_wavelength - initial_wavelength, cfg.get(cfg.WAVEMETER_PRECISION)))
        counter = 1
        file_name = ''

        pl_pipe_in, pl_pipe_out = Pipe()
        pl_plot_process = SpectrumPlotProcess(pipe=pl_pipe_out, daemon=True)
        self.spectrum_plot_processes.append(pl_plot_process)
        pl_plot_process.start()

        # TODO: Make these options configurable
        plot_analysis = True
        integration_start = 720
        integration_end = 800
        if plot_analysis:
            analysis_pipe_in, analysis_pipe_out = Pipe()
            analysis_plot_process = PLEAnalysisPlotProcess(pipe=analysis_pipe_out, daemon=True)
            self.analysis_plot_processes.append(analysis_plot_process)
            analysis_plot_process.start()

        data = {
            'grating_grooves': grating_grooves,
            'center_wavelength': center_wavelength
        }
        for wavelength in wavelengths:
            wavelength = round(float(wavelength), cfg.get(cfg.WAVEMETER_PRECISION))
            self.lock_at_wavelength(wavelength)
            if self.ple_exit_flag:
                print('Received exit signal, saving PLE data.')
                break
            acquisition_data = ccd.take_acquisition()  # FVB mode bins into each column, so this only grabs points along width
            file_name = os.path.join(scan_location, f"{str(counter).zfill(3)}_{scan_name}_{wavelength}nm"
                                                    f"_StepSize_{step}nm_Range_{wavelength_range}nm.txt")
            np.savetxt(file_name, acquisition_data)

            acq_wavelengths = self.pixels_to_wavelengths(range(len(acquisition_data)), center_wavelength, grating_grooves)
            pl_pipe_in.send((acq_wavelengths, acquisition_data))

            if plot_analysis:
                start_pixel, end_pixel = self.find_integration_endpoints(integration_start, integration_end,
                                                                         center_wavelength, grating_grooves)
                analysis_pipe_in.send((wavelength, sum(acquisition_data[start_pixel:end_pixel])))

            data[wavelength] = acquisition_data
            counter += 1

        pl_pipe_in.send(None)
        if file_name:
            self.plot_single_acquisition(center_wavelength, grating_grooves, data_file=file_name)

        with open(data_file_name, 'wb') as data_file:
            pickle.dump(data, data_file, pickle.HIGHEST_PROTOCOL)

    def lock_at_wavelength(self, wavelength: float):
        """Try to lock the Matisse at a given wavelength, waiting to return until we're within a small tolerance."""
        tolerance = 10 ** -cfg.get(cfg.WAVEMETER_PRECISION)
        self.matisse.set_wavelength(wavelength)
        while abs(wavelength - self.matisse.wavemeter_wavelength()) >= tolerance or \
                (self.matisse.is_setting_wavelength or self.matisse.is_scanning_bifi or self.matisse.is_scanning_thin_etalon):
            if self.ple_exit_flag:
                break
            time.sleep(3)

    def stop_ple_tasks(self):
        """Trigger the exit flags to stop running scans and PLE measurements."""
        self.ple_exit_flag = True
        if ccd:
            ccd.exit_flag = True

    def analyze_ple_data(self, analysis_name: str, data_file_path: str, integration_start: float, integration_end: float,
                         background_file_path=''):
        """
        Sum the counts of all spectra for a set of PLE measurements and plot them against wavelength.

        Loads PLE data from {name}.pickle and pickles integrated counts for each wavelength into {name}_analysis.pickle.
        Optionally subtract background from given file name. The background file should be loadable with numpy.loadtxt.

        Parameters
        ----------
        data_file_path
            the path to the .pickle file containing the PLE measurement data
        integration_start
            start of integration region (nm) for tallying the counts
        integration_end
            end of integration region (nm) for tallying the counts
        background_file_path
            the name of a file to use for subtracting background, should be loadable with numpy.loadtxt
        """
        self.ple_exit_flag = False

        if not data_file_path:
            print('WARNING: No data file provided to analyze.')
            return
        if not analysis_name:
            print('WARNING: Name of analysis is required.')
            return

        data_dir = os.path.abspath(os.path.dirname(data_file_path))
        analysis_file_path = os.path.join(data_dir, f"{analysis_name}.pickle")

        if os.path.exists(analysis_file_path):
            print(f"WARNING: An analysis called '{analysis_name}' already exists. Choose a new name and try again.")
            return

        with open(data_file_path, 'rb') as full_data_file:
            scans = pickle.load(full_data_file)

        if background_file_path:
            background_data = np.loadtxt(background_file_path)
        else:
            background_data = None

        center_wavelength = scans.pop('center_wavelength')
        grating_grooves = scans.pop('grating_grooves')
        start_pixel, end_pixel = self.find_integration_endpoints(integration_start, integration_end,
                                                                 center_wavelength, grating_grooves)
        total_counts = {}
        for wavelength in scans.keys():
            if self.ple_exit_flag:
                print('Received exit signal, saving PLE data.')
                break
            if background_data and background_data.any():
                scans[wavelength] = scans[wavelength].astype(np.double)
                scans[wavelength] -= background_data
            total_counts[wavelength] = sum(scans[wavelength][start_pixel:end_pixel])

        with open(analysis_file_path, 'wb') as analysis_file:
            pickle.dump(total_counts, analysis_file, pickle.HIGHEST_PROTOCOL)

        plot_process = PLEAnalysisPlotProcess(total_counts, daemon=True)
        self.analysis_plot_processes.append(plot_process)
        plot_process.start()

    def plot_ple_analysis_file(self, analysis_file_path: str):
        """Plot the PLE analysis data from the given .pickle file."""
        with open(analysis_file_path, 'rb') as analysis_file:
            data = pickle.load(analysis_file)
        plot_process = PLEAnalysisPlotProcess(data, daemon=True)
        self.analysis_plot_processes.append(plot_process)
        plot_process.start()

    def plot_single_acquisition(self, center_wavelength: float, grating_grooves: int, *ccd_args, data_file=None,
                                **ccd_kwargs):
        """
        Plot a single acquisition from the CCD at the given center wavelength and using the grating with the given
        number of grooves. If a data file name is specified, this will skip reading the CCD and just plot the data
        in that file.

        Parameters
        ----------
        center_wavelength
            the wavelength at which to set the spectrometer
        grating_grooves
            the number of grooves to use for the spectrometer grating
        data_file
            file name containing data to plot - if None, will grab data from the CCD
        *ccd_args
            args to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        **ccd_kwargs
            kwargs to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        """
        self.ple_exit_flag = False
        if data_file:
            data = np.loadtxt(data_file)
        else:
            PLE.load_andor_libs()
            print(f"Setting spectrometer grating to {grating_grooves} grvs and center wavelength to {center_wavelength}...")
            shamrock.set_grating_grooves(grating_grooves)
            shamrock.set_center_wavelength(center_wavelength)
            if self.ple_exit_flag:
                return
            ccd.setup(*ccd_args, **ccd_kwargs)
            data = ccd.take_acquisition()

        wavelengths = self.pixels_to_wavelengths(range(len(data)), center_wavelength, grating_grooves)

        plot_process = SpectrumPlotProcess(wavelengths, data, daemon=True)
        self.spectrum_plot_processes.append(plot_process)
        plot_process.start()

    def pixels_to_wavelengths(self, pixels, center_wavelength: float, grating_grooves: int):
        """
        Convert pixels to nanometers using given spectrometer settings.

        Parameters
        ----------
        pixels
            an iterable of pixel indices to be converted to wavelengths
        center_wavelength
            the center wavelength used to take the CCD data
        grating_grooves
            the number of grooves for the grating used to take the CCD data

        Returns
        -------
        ndarray
            an array of wavelengths that each correspond to a pixel on the CCD screen
        """
        nm_per_pixel = Shamrock.GRATINGS_NM_PER_PIXEL[grating_grooves]
        offset = Shamrock.GRATINGS_OFFSET_NM[grating_grooves]
        # Point-slope formula for calculating wavelengths from pixels
        # Use pixel + 1 because indexes range from 0 to 1023, CCD center is at 512 but zero-indexing would put it at 511
        wavelengths = [nm_per_pixel * (pixel + 1 - CCD.WIDTH / 2) + center_wavelength + offset for pixel in pixels]
        return np.array(wavelengths)

    def find_integration_endpoints(self, start_wavelength: float, end_wavelength: float, center_wavelength: float,
                                   grating_grooves: int):
        """
        Convert a starting and ending wavelength to CCD pixels.

        Parameters
        ----------
        start_wavelength
            starting point of integration, in nanometers
        end_wavelength
            ending point of integration, in nanometers
        center_wavelength
            the wavelength at which the spectrometer was set
        grating_grooves
            the number of grooves used for the spectrometer grating

        Returns
        -------
        (int, int)
            the start and end pixels corresponding to the given start and end wavelengths
        """
        nm_per_pixel = Shamrock.GRATINGS_NM_PER_PIXEL[grating_grooves]
        offset = Shamrock.GRATINGS_OFFSET_NM[grating_grooves]
        # Invert pixel -> wavelength conversion
        start_pixel = int(CCD.WIDTH / 2 - 1 + (start_wavelength - center_wavelength - offset) / nm_per_pixel)
        end_pixel = int(CCD.WIDTH / 2 - 1 + (end_wavelength - center_wavelength - offset) / nm_per_pixel)
        return start_pixel, end_pixel

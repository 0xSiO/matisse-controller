import os
import pickle
import time

import numpy as np

import matisse_controller.config as cfg
from matisse_controller.shamrock_ple.ccd import CCD
from matisse_controller.shamrock_ple.shamrock import Shamrock
from matisse_controller.shamrock_ple.plotting import PLEAnalysisPlotProcess

ccd: CCD = None
shamrock: Shamrock = None


class PLE:
    """PLE scanning functionality with the Andor Shamrock and Newton CCD."""

    def __init__(self, matisse):
        self.matisse = matisse
        self.plotting_processes = []

    @staticmethod
    def load_andor_libs():
        global ccd
        global shamrock
        if ccd is None:
            ccd = CCD()
            print('CCD initialized.')
        if shamrock is None:
            shamrock = Shamrock()
            print('Shamrock initialized.')

    def start_ple_scan(self, name: str, initial_wavelength: float, final_wavelength: float, step: float,
                       center_wavelength: float, grating_grooves: int, *ccd_args, **ccd_kwargs):
        """
        Perform a PLE scan using the Andor Shamrock spectrometer and Newton CCD.

        Generates text files with data from each spectrum taken during the scan, and pickles the Python dictionary of
        all data into {name}.pickle.

        Parameters
        ----------
        name
            A unique name to give the PLE measurement. This will be included in the name of all the data files.
        initial_wavelength
            starting wavelength for the PLE scan
        final_wavelength
            ending wavelength for the PLE scan
        step
            the desired change in wavelength between each individual scan
        *ccd_args
            args to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        **ccd_kwargs
            kwargs to pass to `matisse_controller.shamrock_ple.ccd.CCD.setup`
        """
        if not name:
            print('WARNING: Name of PLE scan is required.')
            return

        data_file_name = f"{name}.pickle"

        if os.path.exists(data_file_name):
            print(f"WARNING: A PLE scan has already been run for '{name}'. Choose a new name and try again.")
            return

        PLE.load_andor_libs()
        print(f"Setting spectrometer grating to {grating_grooves} grvs and center wavelength to {center_wavelength}.")
        shamrock.set_grating_grooves(grating_grooves)
        shamrock.set_center_wavelength(center_wavelength)
        ccd.setup(*ccd_args, **ccd_kwargs)
        wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
        wavelength_range = abs(round(final_wavelength - initial_wavelength, cfg.get(cfg.WAVEMETER_PRECISION)))
        counter = 1
        data = {}
        for wavelength in wavelengths:
            wavelength = round(wavelength, cfg.get(cfg.WAVEMETER_PRECISION))
            if self.matisse.exit_flag:
                print('Received exit signal, saving PLE data.')
                break
            self.lock_at_wavelength(wavelength)
            data = ccd.take_acquisition()  # FVB mode bins into each column, so this only grabs points along width
            file_name = f"{str(counter).zfill(3)}_{name}_{round(wavelength, cfg.get(cfg.WAVEMETER_PRECISION))}nm" \
                        f"_StepSize_{step}nm_Range_{wavelength_range}nm.txt"
            np.savetxt(file_name, data)
            data[wavelength] = data
            counter += 1
        with open(data_file_name, 'wb') as data_file:
            pickle.dump(data, data_file, pickle.HIGHEST_PROTOCOL)

    def lock_at_wavelength(self, wavelength: float):
        """Try to lock the Matisse at a given wavelength, waiting to return until we're within a small tolerance."""
        tolerance = 0.001
        self.matisse.set_wavelength(wavelength)
        self.matisse.set_recommended_fast_piezo_setpoint()
        if not self.matisse.laser_locked():
            self.matisse.start_laser_lock_correction()
        while abs(wavelength - self.matisse.wavemeter_wavelength()) >= tolerance:
            time.sleep(3)

    def stop_ple_scan(self):
        """Trigger the Matisse exit_flag to stop running scans and PLE measurements."""
        self.matisse.exit_flag = True

    def analyze_ple_data(self, data_file_path: str, integration_start: float, integration_end: float,
                         background_file_path=''):
        """
        Sum the counts of all spectra for a set of PLE measurements and plot them against wavelength.

        Loads PLE data from {name}.pickle and pickles integrated counts for each wavelength into {name}_analysis.pickle.
        If an analysis file already exists, it will plot that instead.

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
        if not data_file_path:
            print('WARNING: No data file provided to analyze.')
            return

        data_dir = os.path.abspath(os.path.dirname(data_file_path))
        data_file_name = os.path.basename(data_file_path).split('.')[0]
        analysis_file_path = os.path.join(data_dir, f"{data_file_name}_analysis.pickle")

        if os.path.exists(analysis_file_path):
            print(f"Using existing analysis file.")
            with open(analysis_file_path, 'rb') as analysis_file:
                total_counts = pickle.load(analysis_file)
        else:
            print(f"Generating new analysis file.")
            with open(data_file_path, 'rb') as full_data_file:
                scans = pickle.load(full_data_file)

            if background_file_path:
                background_data = np.loadtxt(background_file_path)
            else:
                background_data = None

            # TODO: Figure out index for integration endpoints, then slice scan data
            # TODO: Store/load actual spectrometer center and grating in pickle file
            # center = 740.0
            # start_pixel, end_pixel = self.find_integration_endpoints(integration_start, integration_end, center, 1)

            total_counts = {}
            for wavelength in scans.keys():
                if background_data:
                    scans[wavelength] -= background_data
                total_counts[wavelength] = sum(scans[wavelength])

        with open(analysis_file_path, 'wb') as analysis_file:
            pickle.dump(total_counts, analysis_file, pickle.HIGHEST_PROTOCOL)

        plot_process = PLEAnalysisPlotProcess(total_counts, daemon=True)
        self.plotting_processes.append(plot_process)
        plot_process.start()

    # TODO: Finish this
    def find_integration_endpoints(self, start, end, center, grating):
        return 0, 1023

import os
import pickle
import time

import matplotlib.pyplot as plt
import numpy as np

from matisse_controller.shamrock_ple.ccd import CCD
from matisse_controller.shamrock_ple.constants import *
from matisse_controller.shamrock_ple.shamrock import Shamrock

ccd: CCD = None
shamrock: Shamrock = None


class PLE:
    """PLE scanning functionality with the Andor Shamrock and Newton CCD."""

    # TODO: Currently untested

    def __init__(self, matisse):
        self.matisse = matisse
        global ccd
        global shamrock
        if ccd is None:
            ccd = CCD()
        if shamrock is None:
            shamrock = Shamrock()

    def start_ple_scan(self, name: str, initial_wavelength: float, final_wavelength: float, step: float, *ccd_args,
                       **ccd_kwargs):
        """
        Perform a PLE scan using the Andor Shamrock spectrometer and Newton CCD.

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
        if os.path.exists(f"{name}_full_pickled.dat"):
            raise FileExistsError(
                f"A PLE scan has already been run for '{name}'. Please choose a different name and try again.")

        ccd.setup(*ccd_args, **ccd_kwargs)
        wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
        counter = 1
        scans = {}
        for wavelength in wavelengths:
            if self.matisse.exit_flag:
                print('Received exit signal, saving scan data.')
                break
            self.lock_at_wavelength(wavelength)
            data = ccd.take_acquisition()  # FVB mode bins into each column, so this only grabs points along width
            file_name = f"{str(counter).zfill(3)}_{name}_{wavelength}nm_StepSize_{step}nm_Range_{abs(round(final_wavelength - initial_wavelength, 8))}nm.txt"
            np.savetxt(file_name, data)
            scans[wavelength] = data
            counter += 1
        with open(f"{name}_full_pickled.dat") as full_data_file:
            pickle.dump(scans, full_data_file)

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
        print('Stopping PLE scan.')
        self.matisse.exit_flag = True

    def analyze_ple_data(self, name):
        """Sum the counts of all spectra for a set of PLE measurements and plot them against wavelength."""
        with open(f"{name}_full_pickled.dat") as full_data_file:
            scans = pickle.load(full_data_file)
        # TODO: Subtract noise
        total_counts = {}
        for wavelength in scans.keys():
            total_counts[wavelength] = sum(scans[wavelength])
        plt.plot(total_counts.keys(), total_counts.values())

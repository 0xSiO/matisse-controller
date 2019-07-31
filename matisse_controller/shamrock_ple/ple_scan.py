import time

import numpy as np

from .read_ccd import take_image


# TODO: Use Matisse and Shamrock with CCD to perform the whole process
def do_ple_scan(name, initial_wavelength, final_wavelength, step, exposure_time, matisse):
    """
    Perform a PLE scan using the Andor Shamrock spectrometer.

    :param matisse:
    :type matisse: matisse_controller.Matisse
    """
    # 'Inclusive' arange
    wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
    for wavelength in wavelengths:
        matisse.set_wavelength(wavelength)
        time.sleep(1)  # TODO: Or some configurable amount of time
        take_image()  # TODO: Save to file


# TODO: Grab data from files matching given name and analyze
def analyze_ple_data(name):
    """
    Analyze the data from a PLE scan.

    :param name:
    """

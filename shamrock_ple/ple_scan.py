import os
import time
from ctypes import *

import matplotlib.pyplot as plt
import numpy as np

from matisse_controller import Matisse

ACQ_MODE_SINGLE = 1
ACQ_MODE_ACCUMULATE = 2
ACQ_MODE_KINETICS = 3
ACQ_MODE_FAST_KINETICS = 4
ACQ_MODE_UNTIL_ABORT = 5
READ_MODE_FVB = 0
READ_MODE_MULTI_TRACK = 1
READ_MODE_RANDOM_TRACK = 2
READ_MODE_SINGLE_TRACK = 3
READ_MODE_IMAGE = 4
COSMIC_RAY_FILTER_OFF = 0
COSMIC_RAY_FILTER_ON = 2

os.chdir('lib')
andor: WinDLL  # TODO: andor: WinDLL = windll.LoadLibrary('ATMCD64D.dll')
shamrock: WinDLL = windll.LoadLibrary('ShamrockCIF64.dll')


# TODO: Use Matisse and Shamrock with CCD to perform the whole process
def do_ple_scan(name, initial_wavelength, final_wavelength, step, matisse: Matisse, exposure_time,
                acquisition_mode=ACQ_MODE_ACCUMULATE, readout_mode=READ_MODE_FVB):
    """Perform a PLE scan using the Andor Shamrock spectrometer."""
    setup_spectrometer()
    width, height = setup_ccd(exposure_time, acquisition_mode, readout_mode)
    # 'Inclusive' arange
    wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
    counter = 1
    for wavelength in wavelengths:
        matisse.set_wavelength(wavelength)
        time.sleep(1)  # TODO: Or some configurable amount of time
        data = take_spectrum(width)
        with open(f"{str(counter).zfill(3)}_{name}_{wavelength}nm.txt") as file:
            data.tofile(file)
        counter += 1


def setup_spectrometer():
    shamrock.ShamrockInitialize()
    num_devices = c_int()
    shamrock.ShamrockGetNumberDevices(pointer(num_devices))
    print(num_devices.value, 'Shamrock devices found')
    shamrock.ShamrockClose()


def setup_ccd(exposure_time, acquisition_mode, readout_mode):
    andor.Initialize()
    min_temp, max_temp = c_int(), c_int()
    andor.GetTemperatureRange(pointer(min_temp), pointer(max_temp))
    # TODO: SetTemperature, CoolerON? Cooling should be at -70 C, I think
    current_temp = c_float()
    andor.GetTemperatureF(pointer(current_temp))
    current_temp = current_temp.value
    print(f"Current temp: {current_temp} C")
    # TODO: Once temperature stabilizes...
    andor.SetAcquisitionMode(c_int(acquisition_mode))
    andor.SetReadMode(c_int(readout_mode))
    size_x, size_y = c_int(), c_int()
    andor.GetDetector(pointer(size_x), pointer(size_y))
    andor.SetImage(c_int(1), c_int(1), c_int(1), size_x, c_int(1), size_y)  # use full display
    andor.SetExposureTime(c_float(exposure_time))
    andor.SetFilterMode(c_int(COSMIC_RAY_FILTER_ON))
    return size_x, size_y


# TODO: Grab data from files matching given name and analyze
def analyze_ple_data(name):
    """
    Analyze the data from a PLE scan.

    :param name:
    """


def take_spectrum(num_points):
    andor.StartAcquisition()
    acquiring = True
    while acquiring:
        status = c_int()
        andor.GetStatus(pointer(status))
        if status.value == 20073:  # TODO: Replace with constant
            acquiring = False
        time.sleep(1)
    acquisition_array_type = c_int32 * num_points
    data = acquisition_array_type()
    andor.GetAcquiredData(data, c_int(num_points))
    data = np.array(data, dtype=np.int32)
    plt.plot(range(0, num_points), data)
    return data


if __name__ == '__main__':
    setup_spectrometer()

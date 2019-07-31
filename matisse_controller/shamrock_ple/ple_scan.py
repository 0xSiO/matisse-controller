import os
import pickle
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
TRIGGER_MODE_INTERNAL = 0

os.chdir('lib')
andor: WinDLL  # TODO: andor: WinDLL = windll.LoadLibrary('ATMCD64D.dll')
shamrock: WinDLL = windll.LoadLibrary('ShamrockCIF64.dll')
matisse = Matisse()


def do_ple_scan(name, initial_wavelength, final_wavelength, step, exposure_time, acquisition_mode=ACQ_MODE_ACCUMULATE,
                readout_mode=READ_MODE_FVB, temperature=-70):
    """Perform a PLE scan using the Andor Shamrock spectrometer."""
    setup_spectrometer()
    width, height = setup_ccd(exposure_time, acquisition_mode, readout_mode, temperature)
    # 'Inclusive' arange
    wavelengths = np.append(np.arange(initial_wavelength, final_wavelength, step), final_wavelength)
    counter = 1
    scans = {}
    tolerance = 0.001
    for wavelength in wavelengths:
        matisse.set_wavelength(wavelength)
        while abs(wavelength - matisse.wavemeter_wavelength()) >= tolerance:
            time.sleep(3)
        data = take_spectrum(width)
        file_name = f"{str(counter).zfill(3)}_{name}_{wavelength}nm.txt"
        np.savetxt(file_name, data)
        scans[wavelength] = data
        counter += 1
    with open(f"{name}_full_pickled.dat") as full_data_file:
        pickle.dump(scans, full_data_file)


def setup_spectrometer():
    shamrock.ShamrockInitialize()
    num_devices = c_int()
    shamrock.ShamrockGetNumberDevices(pointer(num_devices))
    print(num_devices.value, 'Shamrock devices found')
    shamrock.ShamrockClose()


def setup_ccd(exposure_time, acquisition_mode, readout_mode, temperature):
    andor.Initialize()
    min_temp, max_temp = c_int(), c_int()
    andor.GetTemperatureRange(pointer(min_temp), pointer(max_temp))
    andor.SetTemperature(c_int(temperature))
    andor.CoolerON()
    current_temp = c_float()
    while current_temp.value > temperature:
        andor.GetTemperatureF(pointer(current_temp))
        current_temp = current_temp.value
        print(f"Cooling CCD. Current temperature is {current_temp} C")
        time.sleep(3)

    if acquisition_mode == ACQ_MODE_ACCUMULATE:
        use_accumulate_mode()
    else:
        andor.SetAcquisitionMode(c_int(acquisition_mode))

    andor.SetReadMode(c_int(readout_mode))
    size_x, size_y = c_int(), c_int()
    andor.GetDetector(pointer(size_x), pointer(size_y))
    andor.SetExposureTime(c_float(exposure_time))
    return size_x.value, size_y.value


def use_accumulate_mode(num_cycles=2, cycle_time=1.025):
    andor.SetAcquisitionMode(ACQ_MODE_ACCUMULATE)
    andor.SetNumberAccumulations(c_int(num_cycles))
    andor.SetAccumulationCycleTime(c_float(cycle_time))
    andor.SetTriggerMode(c_int(TRIGGER_MODE_INTERNAL))
    andor.SetFilterMode(c_int(COSMIC_RAY_FILTER_ON))


def analyze_ple_data(name):
    """
    Analyze the data from a PLE scan.

    :param name:
    """
    scans = {}
    with open(f"{name}_full_pickled.dat") as full_data_file:
        scans = pickle.load(full_data_file)
    # TODO: Integrate and show plot


def take_spectrum(num_points):
    andor.StartAcquisition()
    acquisition_array_type = c_int32 * num_points
    data = acquisition_array_type()
    andor.WaitForAcquisition()
    andor.GetAcquiredData(data, c_int(num_points))
    data = np.array(data, dtype=np.int32)
    plt.plot(range(0, num_points), data)
    return data


if __name__ == '__main__':
    setup_spectrometer()

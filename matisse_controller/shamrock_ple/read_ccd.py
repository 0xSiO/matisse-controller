import os
import time
from ctypes import *

import numpy as np
import matplotlib.pyplot as plt


def main():
    os.chdir('lib')  # TODO: Assume the library is already installed and included in PATH
    shamrock: WinDLL = windll.LoadLibrary('ShamrockCIF64.dll')
    shamrock.ShamrockInitialize()
    num_devices = c_int(0)
    shamrock.ShamrockGetNumberDevices(pointer(num_devices))
    print(num_devices.value, 'Shamrock devices found')
    # TODO: take_image()
    shamrock.ShamrockClose()


def take_image():
    # TODO: andor: WinDLL = windll.LoadLibrary('Andor.dll')
    andor: WinDLL
    andor.Initialize()
    size_x, size_y = c_int(0), c_int(0)
    andor.GetDetector(pointer(size_x), pointer(size_y))
    min_temp, max_temp = c_int(0), c_int(0)
    andor.GetTemperatureRange(pointer(min_temp), pointer(max_temp))
    # TODO: SetTemperature, CoolerON?
    current_temp = c_float(0)
    andor.GetTemperatureF(pointer(current_temp))
    print(f"Current temp: {current_temp.value} C")
    return
    # TODO: Once temperature stabilizes...
    andor.SetAcquisitionMode(c_int(1))  # single scan
    andor.SetReadMode(c_int(4))  # image
    andor.SetImage(c_int(1), c_int(1), c_int(1), size_x, c_int(1), size_y)  # use full display
    andor.SetExposureTime(c_float(0.1))
    andor.StartAcquisition()
    acquiring = True
    while acquiring:
        status = c_int(0)
        andor.GetStatus(pointer(status))
        if status.value == 20073:  # TODO: Replace with constant
            acquiring = False
        time.sleep(1)
    # Done acquiring
    total_size = size_x.value * size_y.value
    acquisition_array_type = c_int32 * total_size
    data = acquisition_array_type()
    # Slurp all the data into one long array
    andor.GetAcquiredData(data, c_int(total_size))
    # Now convert to numpy array and break it into rows and columns
    data = np.array(data, dtype=np.int32).reshape((size_y.value, size_x.value)).transpose()
    plt.imshow(data)


if __name__ == '__main__':
    main()

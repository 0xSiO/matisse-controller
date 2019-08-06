import time
from ctypes import *

import matplotlib.pyplot as plt
import numpy as np

from matisse_controller.shamrock_ple.constants import *
from matisse_controller.shamrock_ple.utils import load_lib


class CCD:
    LIBRARY_NAME = 'atmcd64d.dll'
    WIDTH = 1024
    HEIGHT = 256

    def __init__(self):
        try:
            self.lib = load_lib(CCD.LIBRARY_NAME)
            self.lib.Initialize()
        except OSError as err:
            raise RuntimeError('Unable to initialize Andor CCD API.') from err

    def __del__(self):
        self.shutdown()

    def setup(self, exposure_time: float, acquisition_mode: int, readout_mode: int, temperature: int):
        assert self.lib.Initialize() == CCDErrorCode.DRV_SUCCESS
        num_cameras = c_long()
        self.lib.GetAvailableCameras(pointer(num_cameras))
        print(num_cameras.value, 'CCD cameras found.')

        min_temp, max_temp = c_int(), c_int()
        self.lib.GetTemperatureRange(pointer(min_temp), pointer(max_temp))
        print(f"Min temp: {min_temp}, max temp: {max_temp}")

        self.lib.SetTemperature(c_int(temperature))
        self.lib.CoolerON()
        current_temp = c_float()
        # Cooler stops when temp is within 3 degrees of target, so wait until it's close
        # CCD normally takes a few minutes to fully cool down
        while current_temp.value > temperature + 3.25:
            self.lib.GetTemperatureF(pointer(current_temp))
            current_temp = current_temp.value
            print(f"Cooling CCD. Current temperature is {current_temp} °C")
            time.sleep(5)

        if acquisition_mode == ACQ_MODE_ACCUMULATE:
            self.use_accumulate_mode()
        else:
            self.lib.SetAcquisitionMode(c_int(acquisition_mode))

        self.lib.SetReadMode(c_int(readout_mode))
        self.lib.SetExposureTime(c_float(exposure_time))
        # TODO: Maybe set the vertical/horizontal speeds

    def use_accumulate_mode(self, num_cycles=2, cycle_time=1.025):
        self.lib.SetAcquisitionMode(ACQ_MODE_ACCUMULATE)
        self.lib.SetNumberAccumulations(c_int(num_cycles))
        self.lib.SetAccumulationCycleTime(c_float(cycle_time))
        self.lib.SetTriggerMode(c_int(TRIGGER_MODE_INTERNAL))
        self.lib.SetFilterMode(c_int(COSMIC_RAY_FILTER_ON))

    def take_acquisition(self, num_points) -> np.ndarray:
        self.lib.StartAcquisition()
        acquisition_array_type = c_int32 * num_points
        data = acquisition_array_type()
        self.lib.WaitForAcquisition()
        self.lib.GetAcquiredData(data, c_int(num_points))
        data = np.array(data, dtype=np.int32)
        plt.plot(range(0, num_points), data)
        return data

    def shutdown(self):
        self.lib.CoolerOFF()
        # TODO: Before shutting it down, we MUST wait for temp to hit -20 °C, otherwise it rises too fast for the sensor

import time
from ctypes import *

import numpy as np

import matisse_controller.config as cfg
from matisse_controller.shamrock_ple.constants import *
from matisse_controller.shamrock_ple.utils import load_lib


# TODO: Add action to take single acquisition from CCD
# TODO: Add action to give live feed from CCD
class CCD:
    LIBRARY_NAME = 'atmcd64d.dll'
    WIDTH = 1024
    HEIGHT = 256
    MIN_TEMP = -120
    MAX_TEMP = -10

    def __init__(self):
        try:
            self.lib = load_lib(CCD.LIBRARY_NAME)
            self.lib.Initialize()
            self.lib.SetTemperature(c_int(cfg.get(cfg.PLE_TARGET_TEMPERATURE)))
            self.lib.CoolerON()
            self.temperature_ok = False

            num_cameras = c_long()
            self.lib.GetAvailableCameras(pointer(num_cameras))
            assert num_cameras.value > 0, 'No CCD camera found.'
        except OSError as err:
            raise RuntimeError('Unable to initialize Andor CCD API.') from err

    def __del__(self):
        self.shutdown()

    def setup(self, exposure_time: float, acquisition_mode=ACQ_MODE_SINGLE, readout_mode=READ_MODE_FVB,
              temperature=-70):
        """
        Perform setup procedures on CCD, like cooling down to a given temperature and setting acquisition parameters.

        Parameters
        ----------
        exposure_time
            the desired exposure time at which to configure the CCD
        acquisition_mode
            the desired acquisition mode at which to configure the CCD (default is accumulate)
        readout_mode
            the desired readout mode at which to configure the CCD (default is FVB)
        temperature
            the desired temperature in degrees centigrade at which to configure the CCD (default is -70)
        """
        min_temp, max_temp = c_int(), c_int()
        self.lib.GetTemperatureRange(pointer(min_temp), pointer(max_temp))
        min_temp, max_temp = min_temp.value, max_temp.value
        assert min_temp < temperature < max_temp, f"Temperature must be set between {min_temp} and {max_temp}"

        self.lib.SetTemperature(c_int(temperature))
        self.lib.CoolerON()
        # Cooler stops when temp is within 3 degrees of target, so wait until it's close
        # CCD normally takes a few minutes to fully cool down
        while not self.temperature_ok:
            current_temp = self.get_temperature()
            print(f"Cooling CCD. Current temperature is {round(current_temp, 2)} °C")
            self.temperature_ok = current_temp < temperature + cfg.get(cfg.PLE_TEMPERATURE_TOLERANCE)
            time.sleep(10)

        print('Configuring acquisition parameters.')
        self.lib.SetAcquisitionMode(c_int(acquisition_mode))
        self.lib.SetReadMode(c_int(readout_mode))
        self.lib.SetVSSpeed(c_int(1))
        self.lib.SetTriggerMode(c_int(TRIGGER_MODE_INTERNAL))
        self.lib.SetExposureTime(c_float(exposure_time))
        print('CCD ready for acquisition.')

    def get_temperature(self) -> float:
        temperature = c_float()
        self.lib.GetTemperatureF(pointer(temperature))
        return temperature.value

    def take_acquisition(self, num_points=1024) -> np.ndarray:
        self.lib.StartAcquisition()
        acquisition_array_type = c_int32 * num_points
        data = acquisition_array_type()
        # self.lib.WaitForAcquisition() does not work, so use a loop instead and check the status.
        while True:
            status = c_int()
            self.lib.GetStatus(pointer(status))
            if status.value == CCDErrorCode.DRV_IDLE.value:
                break
            else:
                time.sleep(1)
        self.lib.GetAcquiredData(data, c_int(num_points))
        data = np.array(data, dtype=np.int32)
        return data

    def shutdown(self):
        self.lib.CoolerOFF()
        # TODO: Before shutting it down, we should wait for temp to hit -20 °C, otherwise it rises too fast
        # In practice, of course, we don't do this :)

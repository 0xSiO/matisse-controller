from ctypes import *

from matisse_controller.shamrock_ple.utils import load_lib


# TODO: Note that for some reason the Shamrock will not be found unless SOLIS is installed. Probably a driver issue :(
class Shamrock:
    LIBRARY_NAME = 'ShamrockCIF.dll'
    DEVICE_ID = c_int(0)

    # Below constants are calculated using a calibrated wavelength axis on SOLIS (end - start) / 1024
    GRATING_300_GRV_NM_PER_PIXEL = 0.116523437
    GRATING_1200_GRV_NM_PER_PIXEL = 0.0273535156
    GRATING_1800_GRV_NM_PER_PIXEL = 0.01578125

    def __init__(self):
        try:
            self.lib = load_lib(Shamrock.LIBRARY_NAME)
            self.lib.ShamrockInitialize()

            num_devices = c_int()
            self.lib.ShamrockGetNumberDevices(pointer(num_devices))
            assert num_devices.value > 0, 'No spectrometer found.'
        except OSError as err:
            raise RuntimeError('Unable to initialize Andor Shamrock API.') from err

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.lib.ShamrockClose()

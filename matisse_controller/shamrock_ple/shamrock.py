from ctypes import *

from matisse_controller.shamrock_ple.utils import load_lib


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
        except OSError as err:
            raise RuntimeError('Unable to initialize Andor Shamrock API.') from err

    def __del__(self):
        self.shutdown()

    def shutdown(self):
        self.lib.ShamrockClose()

    def print_misc_info(self):
        num_devices = c_int()
        self.lib.ShamrockGetNumberDevices(pointer(num_devices))
        print(num_devices.value, 'Shamrock devices found')
        num_pixels = c_int()
        self.lib.ShamrockGetNumberPixels(Shamrock.DEVICE_ID, pointer(num_pixels))
        print(num_pixels.value, 'pixels available')
        pixel_width = c_float()
        self.lib.ShamrockGetPixelWidth(Shamrock.DEVICE_ID, pointer(pixel_width))
        print(pixel_width.value, 'micrometers per pixel')

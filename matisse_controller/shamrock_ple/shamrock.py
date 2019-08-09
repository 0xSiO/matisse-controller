from ctypes import *

from matisse_controller.shamrock_ple.utils import load_lib


# TODO: Note that for some reason the Shamrock will not be found unless SOLIS is installed. Probably a driver issue :(
class Shamrock:
    LIBRARY_NAME = 'ShamrockCIF.dll'
    DEVICE_ID = c_int(0)

    # Below constants are calculated using a pre-calibrated wavelength axis on SOLIS (end - start) / 1024
    GRATINGS_NM_PER_PIXEL = {
        300: 0.116523437,
        1200: 0.0273535156,
        1800: 0.01578125
    }

    def __init__(self):
        self.gratings = {}
        try:
            self.lib = load_lib(Shamrock.LIBRARY_NAME)
            self.lib.ShamrockInitialize()

            num_devices = c_int()
            self.lib.ShamrockGetNumberDevices(pointer(num_devices))
            assert num_devices.value > 0, 'No spectrometer found.'

            self.setup_grating_info()
        except OSError as err:
            raise RuntimeError('Unable to initialize Andor Shamrock API.') from err

    def __del__(self):
        self.shutdown()

    def setup_grating_info(self):
        number = c_int()
        self.lib.ShamrockGetNumberGratings(Shamrock.DEVICE_ID, pointer(number))
        for i in range(1, number + 1):
            # TODO: Check possible issues using c_char_p with no initialization
            lines, blaze, home, offset = c_float(), c_char_p(), c_int(), c_int()
            self.lib.ShamrockGetGratingInfo(Shamrock.DEVICE_ID, c_int(i), pointer(lines), blaze, pointer(home),
                                            pointer(offset))
            print(f"Blaze is {blaze.value}")  # TODO: For debug purposes. Remove later
            self.gratings[lines] = i

    def set_grating_grooves(self, num_grooves: int):
        self.lib.ShamrockSetGrating(Shamrock.DEVICE_ID, c_int(self.gratings[num_grooves]))

    def set_center_wavelength(self, wavelength: float):
        self.lib.ShamrockSetWavelength(Shamrock.DEVICE_ID, c_float(wavelength))

    def shutdown(self):
        self.lib.ShamrockClose()

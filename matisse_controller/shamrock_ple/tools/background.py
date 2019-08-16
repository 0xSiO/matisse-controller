import numpy as np
from scipy.signal import savgol_filter

import matisse_controller.config as cfg
import matisse_controller.shamrock_ple.ple as ple


def take_background(number):
    ple.PLE.load_andor_libs()
    cfg.set(cfg.PLE_TEMPERATURE_TOLERANCE, 4)
    ple.ccd.setup(0.1)

    for i in range(number):
        data = ple.ccd.take_acquisition()
        np.savetxt(f"{str(i + 1).zfill(3)}_background_0.1s.txt.gz", data)


def read_background(number):
    total = np.zeros(1024)
    for i in range(number):
        data = np.loadtxt(f"{str(i + 1).zfill(3)}_background_0.1s.txt.gz")
        total += data
    return total


def smooth(data):
    return savgol_filter(data, window_length=71, polyorder=3)

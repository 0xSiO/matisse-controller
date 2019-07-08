from matisse import Matisse
import time
import random


# TODO: Make this an instance method of Matisse
def stabilize(matisse, tolerance):
    """Keep the difference between desired wavelength and measured wavelength within a given tolerance."""
    while True:
        # drift = matisse.bifi_wavelength() - matisse.wavemeter_wavelength()
        drift = random.random() - 0.5
        if abs(drift) > tolerance:
            if drift < 0:
                # measured wavelength is too high
                print("Wavelength too high, decreasing. Drift is " + str(drift))
            else:
                # measured wavelength is too low
                print("Wavelength too low, increasing. Drift is " + str(drift))
        else:
            print("Wavelength within tolerance. Drift is " + str(drift))
        time.sleep(0.1)


stabilize(None, 0.2)

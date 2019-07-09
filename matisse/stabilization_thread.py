import threading
import time

from queue import Queue


class StabilizationThread(threading.Thread):
    CORRECTION_STEP = 0.001

    def __init__(self, matisse, tolerance: float, delay: float, messages: Queue):
        """
        Initialize stabilization thread with parameters for stabilization loop.

        :param matisse: instance of Matisse to which we should send commands
        :type matisse: matisse.Matisse
        :param tolerance: the maximum allowed drift in measured wavelength from BiFi wavelength
        :param delay: the time to wait between each stabilization loop
        :param messages: a message queue for this thread
        """
        super().__init__()
        self.matisse = matisse
        self.tolerance = tolerance
        self.delay = delay
        self.messages = messages

    def run(self) -> None:
        """
        Try to keep the measured wavelength within the given tolerance by adjusting the reference cell.

        Exits if anything is pushed to the message queue.
        """
        # TODO: Decide whether to keep locking code here or move to Matisse class
        self.matisse.lock_thin_etalon()
        self.matisse.lock_piezo_etalon()
        self.matisse.lock_slow_piezo()
        self.matisse.lock_fast_piezo()
        print(f"Stabilizing laser at {self.matisse.bifi_wavelength()} nm...")
        while True:
            if self.messages.empty():
                drift = self.matisse.bifi_wavelength() - self.matisse.wavemeter_wavelength()
                if abs(drift) > self.tolerance:
                    # TODO: Try doing a SCAN:STATUS RUN instead of setting motor position directly?
                    if drift < 0:
                        # measured wavelength is too high
                        print(f"Wavelength too high, decreasing. Drift is {drift}")
                    else:
                        # measured wavelength is too low
                        print(f"Wavelength too low, increasing. Drift is {drift}")
                else:
                    print(f"Wavelength within tolerance. Drift is {drift}")
                time.sleep(self.delay)
            else:
                self.matisse.unlock_fast_piezo()
                self.matisse.unlock_slow_piezo()
                self.matisse.unlock_piezo_etalon()
                self.matisse.unlock_thin_etalon()
                return

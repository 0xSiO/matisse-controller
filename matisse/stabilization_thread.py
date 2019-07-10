import threading
import time

from queue import Queue


class StabilizationThread(threading.Thread):
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
        self.matisse.query('SCAN:STATUS RUN')
        while True:
            if self.messages.empty():
                drift = self.matisse.bifi_wavelength() - self.matisse.wavemeter_wavelength()
                if abs(drift) > self.tolerance:
                    if drift < 0:
                        # measured wavelength is too high
                        print(f"Wavelength too high, decreasing. Drift is {drift}")
                        self.matisse.query('SCAN:MODE 1')
                    else:
                        # measured wavelength is too low
                        print(f"Wavelength too low, increasing.  Drift is {drift}")
                        self.matisse.query('SCAN:MODE 0')
                else:
                    print(f"Wavelength within tolerance.     Drift is {drift}")
                time.sleep(self.delay)
            else:
                self.matisse.query('SCAN:STATUS STOP')
                return

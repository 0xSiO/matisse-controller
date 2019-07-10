import threading
import time

from queue import Queue


class StabilizationThread(threading.Thread):
    def __init__(self, matisse, wavelength: float, tolerance: float, delay: float, messages: Queue):
        """
        Initialize stabilization thread with parameters for stabilization loop.

        :param matisse: instance of Matisse to which we should send commands
        :type matisse: matisse.Matisse
        :param tolerance: the maximum allowed drift in measured wavelength from BiFi wavelength
        :param delay: the time to wait between each stabilization loop
        :param messages: a message queue for this thread
        """
        super().__init__(daemon=True)
        self.matisse = matisse
        self.desired_wavelength = wavelength
        self.tolerance = tolerance
        self.delay = delay
        self.messages = messages

    def run(self) -> None:
        """
        Try to keep the measured wavelength within the given tolerance by adjusting the reference cell.

        Exits if anything is pushed to the message queue.
        """
        while True:
            if self.messages.empty():
                drift = self.desired_wavelength - self.matisse.wavemeter_wavelength()
                if abs(drift) > self.tolerance:
                    if drift < 0:
                        # measured wavelength is too high
                        print(f"Too high, decreasing. Drift is {drift}, RefCell pos {self.matisse.query('SCAN:NOW?', numeric_result=True)}")
                        next_pos = self.matisse.query('SCAN:NOW?', numeric_result=True) - 0.001
                        # TODO: Don't just check the refcell limit, check all the piezos and correct if needed
                        if next_pos > 0.05:
                            # TODO: Use Matisse#set_refcell_pos
                            # self.matisse.query(f"SCAN:NOW {next_pos}")
                            pass
                    else:
                        # measured wavelength is too low
                        print(f"Too low, increasing.   Drift is {drift}, RefCell pos {self.matisse.query('SCAN:NOW?', numeric_result=True)}")
                        next_pos = self.matisse.query('SCAN:NOW?', numeric_result=True) + 0.001
                        if next_pos < 0.7:
                            # self.matisse.query(f"SCAN:NOW {next_pos}")
                            pass
                else:
                    print(f"Within tolerance.      Drift is {drift}, RefCell pos {self.matisse.query('SCAN:NOW?', numeric_result=True)}")
                time.sleep(self.delay)
            else:
                return

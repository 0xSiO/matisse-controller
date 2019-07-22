import threading
import time
from queue import Queue


class StabilizationThread(threading.Thread):
    REFCELL_ADJUSTMENT_STEP = 0.001
    DRIFT_PRECISION = 4

    def __init__(self, matisse, tolerance: float, delay: float, messages: Queue, *args, **kwargs):
        """
        Initialize stabilization thread with parameters for stabilization loop.

        :param matisse: instance of Matisse to which we should send commands
        :type matisse: matisse.Matisse
        :param tolerance: the maximum allowed drift in measured wavelength from BiFi wavelength
        :param delay: the time to wait between each stabilization loop
        :param messages: a message queue for this thread
        """
        super().__init__(*args, **kwargs)
        self._matisse = matisse
        self._tolerance = tolerance
        self._delay = delay
        self.messages = messages

    def run(self):
        """
        Try to keep the measured wavelength within the given tolerance by adjusting the reference cell.

        Exit if anything is pushed to the message queue.
        """
        while True:
            if self.messages.qsize() == 0:
                drift = self._matisse.target_wavelength - self._matisse.wavemeter_wavelength()
                drift = round(drift, StabilizationThread.DRIFT_PRECISION)
                if abs(drift) > self._tolerance:
                    if drift < 0:
                        # measured wavelength is too high
                        print(f"Too high, decreasing. Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                        if not self._matisse.is_any_limit_reached():
                            next_pos = self._matisse.query('SCAN:NOW?', numeric_result=True) - StabilizationThread.REFCELL_ADJUSTMENT_STEP
                            self._matisse.query(f"SCAN:NOW {next_pos}")
                        else:
                            print('WARNING: A component has hit a limit while adjusting the RefCell. '
                                  'Attempting automatic corrections.')
                            self._matisse.reset_stabilization_piezos()
                    else:
                        # measured wavelength is too low
                        print(f"Too low, increasing.   Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                        if not self._matisse.is_any_limit_reached():
                            next_pos = self._matisse.query('SCAN:NOW?', numeric_result=True) + StabilizationThread.REFCELL_ADJUSTMENT_STEP
                            self._matisse.query(f"SCAN:NOW {next_pos}")
                        else:
                            print('WARNING: A component has hit a limit while adjusting the RefCell. '
                                  'Attempting automatic corrections.')
                            self._matisse.reset_stabilization_piezos()
                else:
                    print(f"Within tolerance.      Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                time.sleep(self._delay)
            else:
                break

import threading
import time
from queue import Queue

from .laser_locked import LaserLocked


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
        super().__init__(daemon=True)
        self._matisse = matisse
        self._tolerance = tolerance
        self._delay = delay
        self._messages = messages

    def run(self):
        """
        Try to keep the measured wavelength within the given tolerance by adjusting the reference cell.

        Exit if anything is pushed to the message queue.
        """
        with LaserLocked(self._matisse):
            while True:
                if self._messages.qsize() == 0:
                    drift = self._matisse.target_wavelength - self._matisse.wavemeter_wavelength()
                    if abs(drift) > self._tolerance:
                        if drift < 0:
                            # measured wavelength is too high
                            print(f"Too high, decreasing. Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                            if not self.limits_reached():
                                next_pos = self._matisse.query('SCAN:NOW?', numeric_result=True) - 0.001
                                self._matisse.set_refcell_pos(next_pos)
                            else:
                                print('WARNING: One or more motor limits have been reached. Stopping stabilization for manual correction.')
                                break
                        else:
                            # measured wavelength is too low
                            print(f"Too low, increasing.   Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                            if not self.limits_reached():
                                next_pos = self._matisse.query('SCAN:NOW?', numeric_result=True) + 0.001
                                self._matisse.set_refcell_pos(next_pos)
                            else:
                                print('WARNING: One or more motor limits have been reached. Stopping stabilization for manual correction.')
                                break
                    else:
                        print(f"Within tolerance.      Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                    time.sleep(self._delay)
                else:
                    break

    def limits_reached(self):
        current_refcell_pos = self._matisse.query('SCAN:NOW?', numeric_result=True)
        current_slow_pz_pos = self._matisse.query('SLOWPIEZO:NOW?', numeric_result=True)
        current_pz_eta_pos = self._matisse.query('PIEZOETALON:BASELINE?', numeric_result=True)

        # During stabilization, we don't want to hit the true limits of any component, so reduce the range slightly
        offset = 0.05
        return (self._matisse.REFERENCE_CELL_LOWER_LIMIT + offset < current_refcell_pos < self._matisse.REFERENCE_CELL_UPPER_LIMIT - offset
               and self._matisse.SLOW_PIEZO_LOWER_LIMIT + offset < current_slow_pz_pos < self._matisse.SLOW_PIEZO_UPPER_LIMIT - offset
               and self._matisse.PIEZO_ETALON_LOWER_LIMIT + offset < current_pz_eta_pos < self._matisse.PIEZO_ETALON_UPPER_LIMIT - offset)

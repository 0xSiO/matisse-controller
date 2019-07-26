import threading
import time
from queue import Queue
import matisse_controller.config as cfg


class StabilizationThread(threading.Thread):
    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        """
        Initialize stabilization thread.

        :param matisse: instance of Matisse to which we should send commands
        :type matisse: matisse.Matisse
        :param messages: a message queue for this thread
        """
        super().__init__(*args, **kwargs)
        self._matisse = matisse
        self.messages = messages
        # Stop any running scans just in case
        self._matisse.stop_scan()
        self._matisse.query(f"SCAN:RISINGSPEED {cfg.get(cfg.STABILIZATION_RISING_SPEED)}")
        self._matisse.query(f"SCAN:FALLINGSPEED {cfg.get(cfg.STABILIZATION_FALLING_SPEED)}")

    def run(self):
        """
        Try to keep the measured wavelength within the configured tolerance by scanning the reference cell.

        Exit if anything is pushed to the message queue.
        """
        while True:
            if self.messages.qsize() == 0:
                drift = self._matisse.target_wavelength - self._matisse.wavemeter_wavelength()
                drift = round(drift, cfg.get(cfg.WAVEMETER_PRECISION))
                if abs(drift) > cfg.get(cfg.STABILIZATION_TOLERANCE):
                    if drift < 0:
                        # measured wavelength is too high
                        print(f"Too high, decreasing. Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                        if not self._matisse.is_any_limit_reached():
                            self._matisse.start_scan(self._matisse.SCAN_MODE_DOWN)
                        else:
                            print('WARNING: A component has hit a limit while adjusting the RefCell. '
                                  'Attempting automatic corrections.')
                            self._matisse.stop_scan()
                            self._matisse.reset_stabilization_piezos()
                    else:
                        # measured wavelength is too low
                        print(f"Too low, increasing.   Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                        if not self._matisse.is_any_limit_reached():
                            self._matisse.start_scan(self._matisse.SCAN_MODE_UP)
                        else:
                            print('WARNING: A component has hit a limit while adjusting the RefCell. '
                                  'Attempting automatic corrections.')
                            self._matisse.stop_scan()
                            self._matisse.reset_stabilization_piezos()
                else:
                    self._matisse.stop_scan()
                    print(f"Within tolerance.      Drift is {drift}, RefCell pos {self._matisse.query('SCAN:NOW?', numeric_result=True)}")
                time.sleep(cfg.get(cfg.STABILIZATION_DELAY))
            else:
                self._matisse.stop_scan()
                break

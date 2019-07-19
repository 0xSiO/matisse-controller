import multiprocessing
from queue import Queue

from matisse.laser_locked import LaserLocked


class LockCorrectionProcess(multiprocessing.Process):
    """
    Runs while the fast piezo attempts to obtain a lock. Exits if the laser cannot lock within a certain timeout, or if
    a component reaches its limit while trying to lock. If the laser locks within the timeout, but a component has
    reached its limit, makes an automatic correction to the slow piezo, piezo etalon, and RefCell.

    TODO: Set recommended setpoint for fast piezo
    """

    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matisse = matisse
        self.messages = messages

    def run(self):
        with LaserLocked(self.matisse):
            while True:
                if self.messages.qsize() == 0:
                    pass
                else:
                    break

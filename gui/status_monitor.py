from contextlib import AbstractContextManager
from queue import Queue

from PyQt5.QtWidgets import QLabel

from .threading import StatusUpdateThread, ExitFlag


class StatusMonitor(QLabel):
    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_thread = StatusUpdateThread(matisse, messages, parent=self)
        self.update_thread.status_read.connect(self.setText)
        self.update_thread.start()


class MotorStatusPaused(AbstractContextManager):
    def __init__(self, monitor: StatusMonitor):
        self.monitor = monitor

    def __enter__(self):
        # TODO: Maybe set a flag to only update wavemeter reading
        self.monitor.update_thread.stop()
        print('Stopped status monitor.')

    def __exit__(self, exc_type, exc_val, exc_tb):
        # TODO: I don't think you can just start it again. Consider a less destructive method for stopping it.
        self.monitor.update_thread.start()
        print('Started status monitor.')

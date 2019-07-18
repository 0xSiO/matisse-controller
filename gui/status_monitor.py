from queue import Queue

from PyQt5.QtWidgets import QLabel

from .threading import StatusUpdateThread


class StatusMonitor(QLabel):
    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_thread = StatusUpdateThread(matisse, messages, parent=self)
        self.update_thread.status_read.connect(self.setText)
        self.update_thread.start()

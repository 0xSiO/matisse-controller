from queue import Queue

from PyQt5.QtWidgets import QLabel

from .threading import StatusUpdateThread, ExitFlag


class StatusMonitor(QLabel):
    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = messages
        self.update_thread = StatusUpdateThread(matisse, messages, parent=self)
        self.update_thread.status_read.connect(self.setText)
        self.update_thread.start()

    def clean_up(self):
        self.messages.put(ExitFlag())
        self.update_thread.wait()

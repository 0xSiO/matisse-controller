from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from gui.threading import ExitFlag


class LoggingThread(QThread):
    """
    A QThread which waits for data to come through a Queue. It blocks until data is available, then sends it to the UI
    thread by emitting a Qt signal.

    Do not implement Qt slots in this class as they will be executed in the creating thread for this class.
    """
    message_received = pyqtSignal(str)

    def __init__(self, queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def run(self):
        while True:
            message = self.queue.get()
            if isinstance(message, ExitFlag):
                break
            else:
                self.message_received.emit(message)

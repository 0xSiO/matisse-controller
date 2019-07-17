from queue import Queue

from PyQt5.QtCore import pyqtSignal, QThread


class LoggingStream:
    """A basic stream that is meant to replace sys.stdout."""

    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)


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
            text = self.queue.get()
            if isinstance(text, LoggingExitFlag):
                break
            else:
                self.message_received.emit(text)


class LoggingExitFlag:
    """Push an instance of this class to the logging queue to exit from the LoggingThread event loop."""
    pass

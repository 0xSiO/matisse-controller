from queue import Queue

from PyQt5.QtCore import pyqtSignal, QThread


# Stream to replace sys.stdout
class LoggingStream:
    def __init__(self, queue: Queue):
        self.queue = queue

    def write(self, text):
        self.queue.put(text)


# A QThread which waits for data to come through a Queue. It blocks until data is available, then sends it to the UI
# thread by emitting a Qt signal.
#
# Do not implement Qt slots in this class as they will be executed in the creating thread for this class.
class LoggingThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, queue: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue = queue

    def run(self):
        while True:
            # TODO: Consider implementing a graceful exit, currently this thread just gets terminated on program exit
            text = self.queue.get()
            self.message_received.emit(text)

import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal


# TODO: Abstract out these threads into another class: BreakableThread

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


class WavelengthUpdateThread(QThread):
    wavelength_read = pyqtSignal(str)

    def __init__(self, wavemeter, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wavemeter = wavemeter
        self.messages = messages

    def run(self):
        wavelength = 'Wavelength: 0.000'
        while True:
            if self.messages.empty():
                # TODO: Read wavelength from wavemeter and format it
                self.wavelength_read.emit(wavelength)
                time.sleep(1)
            else:
                break


class ExitFlag:
    pass

import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal


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

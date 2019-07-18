from queue import Queue

from PyQt5.QtWidgets import QLabel

from .threading import WavelengthUpdateThread


class WavelengthMonitor(QLabel):
    def __init__(self, wavemeter, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_thread = WavelengthUpdateThread(wavemeter, messages, parent=self)
        self.update_thread.wavelength_read.connect(self.setText)
        self.update_thread.start()
        self.setMinimumHeight(30)

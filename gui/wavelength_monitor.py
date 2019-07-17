from queue import Queue

from PyQt5.QtWidgets import QLabel

from .threading import WavelengthUpdateThread, ExitFlag


class WavelengthMonitor(QLabel):
    def __init__(self, wavemeter, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.update_thread = WavelengthUpdateThread(wavemeter, Queue(maxsize=1), parent=self)
        self.update_thread.start()
        self.update_thread.wavelength_read.connect(self.setText)
        self.setMinimumHeight(30)

    def __del__(self):
        self.update_thread.messages.put(ExitFlag)

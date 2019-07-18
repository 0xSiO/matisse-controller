import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from matisse import Matisse


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


class StatusUpdateThread(QThread):
    status_read = pyqtSignal(str)

    def __init__(self, matisse: Matisse, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.matisse = matisse
        self.messages = messages

    def run(self):
        while True:
            if self.messages.qsize() == 0:
                try:
                    bifi_pos = self.matisse.query('MOTBI:POS?', numeric_result=True)
                    thin_eta_pos = self.matisse.query('MOTTE:POS?', numeric_result=True)
                    pz_eta_pos = self.matisse.query('PIEZOETALON:BASELINE?', numeric_result=True)
                    slow_pz_pos = self.matisse.query('SLOWPIEZO:NOW?', numeric_result=True)
                    refcell_pos = self.matisse.query('SCAN:NOW?', numeric_result=True)
                    wavelength = self.matisse.wavemeter.get_raw_value()
                    # TODO: Colors based on how close we are to limits
                    status = f"BiFi:{bifi_pos} Thin Eta:{thin_eta_pos} Pz Eta:{pz_eta_pos} Slow Pz:{slow_pz_pos} \
                    RefCell:{refcell_pos} Wavemeter:{wavelength}"
                except Exception:
                    status = 'Error reading the status.'
                self.status_read.emit(status)
                time.sleep(1)
            else:
                break


class ExitFlag:
    pass

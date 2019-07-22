import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from gui import utils
from gui.threading import ExitFlag


class StatusUpdateThread(QThread):
    status_read = pyqtSignal(str)

    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        """
        TODO: Documentation

        :param matisse:
        :type matisse: matisse.Matisse
        :param messages:
        :param args:
        :param kwargs:
        """
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
                    is_locked = self.matisse.fast_piezo_locked()
                    wavemeter_value = self.matisse.wavemeter.get_raw_value()

                    bifi_pos_text = f"BiFi:{bifi_pos}"
                    thin_eta_pos_text = f"Thin Eta:{thin_eta_pos}"
                    pz_eta_pos_text = f"Pz Eta:{pz_eta_pos}"
                    slow_pz_pos_text = f"Slow Pz:{slow_pz_pos}"
                    refcell_pos_text = f"RefCell:{refcell_pos}"
                    locked_text = f"{utils.green_text('LOCKED') if is_locked else utils.red_text('NO LOCK')}"
                    wavemeter_text = f"Wavemeter:{wavemeter_value}"

                    offset = 0.05
                    refcell_ok = self.matisse.REFERENCE_CELL_LOWER_LIMIT + offset < refcell_pos < self.matisse.REFERENCE_CELL_UPPER_LIMIT - offset
                    slow_pz_ok = self.matisse.SLOW_PIEZO_LOWER_LIMIT + offset < slow_pz_pos < self.matisse.SLOW_PIEZO_UPPER_LIMIT - offset
                    pz_eta_ok = self.matisse.PIEZO_ETALON_LOWER_LIMIT + offset < pz_eta_pos < self.matisse.PIEZO_ETALON_UPPER_LIMIT - offset

                    if not refcell_ok:
                        refcell_pos_text = utils.red_text(refcell_pos_text)
                    if not slow_pz_ok:
                        slow_pz_pos_text = utils.red_text(slow_pz_pos_text)
                    if not pz_eta_ok:
                        pz_eta_pos_text = utils.red_text(pz_eta_pos_text)

                    status = f"{bifi_pos_text} | {thin_eta_pos_text} | {pz_eta_pos_text} | {slow_pz_pos_text} | {refcell_pos_text} | {locked_text} | {wavemeter_text}"
                except Exception:
                    status = utils.red_text('Error reading system status. Please restart if this issue persists.')
                self.status_read.emit(status)
                time.sleep(1)
            else:
                break

    def stop(self):
        self.messages.put(ExitFlag())
        self.wait()

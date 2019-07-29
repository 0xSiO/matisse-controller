import time
from queue import Queue

from PyQt5.QtCore import QThread, pyqtSignal

from matisse_controller.gui.utils import red_text, orange_text, green_text
from matisse_controller.gui.threads import ExitFlag


class StatusUpdateThread(QThread):
    """
    A QThread that periodically reads several pieces of state data and emits all of it in one HTML-formatted string.
    The interval between successive updates is specified by INTERVAL.

    Some messages are colored, like for components that are at or nearing their limits.

    Note: Any Qt slots implemented in this class will be executed in the creating thread for instances of this class.
    """
    status_read = pyqtSignal(str)
    INTERVAL = 1

    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        """
        Initialize an instance of StatusUpdateThread.

        :param matisse: an instance of Matisse
        :type matisse: matisse.Matisse
        :param messages: a message queue
        :param args: args to pass to QThread.__init__
        :param kwargs: kwargs to pass to QThread.__init__
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
                    is_stabilizing = self.matisse.is_stabilizing()
                    is_scanning = self.matisse.is_scanning()
                    is_locked = self.matisse.laser_locked()
                    wavemeter_value = self.matisse.wavemeter.get_raw_value()

                    bifi_pos_text = f"BiFi:{bifi_pos}"
                    thin_eta_pos_text = f"Thin Eta:{thin_eta_pos}"
                    pz_eta_pos_text = f"Pz Eta:{pz_eta_pos:.3f}"
                    slow_pz_pos_text = f"Slow Pz:{slow_pz_pos:.3f}"
                    refcell_pos_text = f"RefCell:{refcell_pos:.3f}"
                    stabilizing_text = f"Stabilize:{green_text('ON') if is_stabilizing else red_text('OFF')}"
                    scanning_text = f"Scanning:{green_text('ON') if is_stabilizing else red_text('OFF')}"
                    locked_text = f"{green_text('LOCKED') if is_locked else red_text('NO LOCK')}"
                    wavemeter_text = f"Wavemeter:{wavemeter_value}"

                    # TODO: Make these constants configurable
                    limit_offset = 0.05
                    refcell_at_limit = not self.matisse.REFERENCE_CELL_LOWER_LIMIT + limit_offset < refcell_pos < self.matisse.REFERENCE_CELL_UPPER_LIMIT - limit_offset
                    slow_pz_at_limit = not self.matisse.SLOW_PIEZO_LOWER_LIMIT + limit_offset < slow_pz_pos < self.matisse.SLOW_PIEZO_UPPER_LIMIT - limit_offset
                    pz_eta_at_limit = not self.matisse.PIEZO_ETALON_LOWER_LIMIT + limit_offset < pz_eta_pos < self.matisse.PIEZO_ETALON_UPPER_LIMIT - limit_offset
                    warn_offset = 0.15
                    refcell_near_limit = not self.matisse.REFERENCE_CELL_LOWER_LIMIT + warn_offset < refcell_pos < self.matisse.REFERENCE_CELL_UPPER_LIMIT - warn_offset
                    slow_pz_near_limit = not self.matisse.SLOW_PIEZO_LOWER_LIMIT + warn_offset < slow_pz_pos < self.matisse.SLOW_PIEZO_UPPER_LIMIT - warn_offset
                    pz_eta_near_limit = not self.matisse.PIEZO_ETALON_LOWER_LIMIT + warn_offset < pz_eta_pos < self.matisse.PIEZO_ETALON_UPPER_LIMIT - warn_offset

                    if refcell_at_limit:
                        refcell_pos_text = red_text(refcell_pos_text)
                    elif refcell_near_limit:
                        refcell_pos_text = orange_text(refcell_pos_text)

                    if slow_pz_at_limit:
                        slow_pz_pos_text = red_text(slow_pz_pos_text)
                    elif slow_pz_near_limit:
                        slow_pz_pos_text = orange_text(slow_pz_pos_text)

                    if pz_eta_at_limit:
                        pz_eta_pos_text = red_text(pz_eta_pos_text)
                    elif pz_eta_near_limit:
                        pz_eta_pos_text = orange_text(pz_eta_pos_text)

                    status = f"{bifi_pos_text} | {thin_eta_pos_text} | {pz_eta_pos_text} | {slow_pz_pos_text} | {refcell_pos_text} | {stabilizing_text} | {scanning_text} | {locked_text} | {wavemeter_text}"
                except Exception:
                    status = red_text('Error reading system status. Please restart if this issue persists.')
                self.status_read.emit(status)
                time.sleep(StatusUpdateThread.INTERVAL)
            else:
                break

    def stop(self):
        self.messages.put(ExitFlag())
        self.wait()

from queue import Queue

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit

from gui import utils
from gui.threading import LoggingThread, ExitFlag


class LoggingArea(QTextEdit):
    def __init__(self, messages: Queue, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.messages = messages
        self.update_thread = LoggingThread(messages)
        self.update_thread.message_received.connect(self.log_message)
        self.update_thread.start()

    @pyqtSlot(str)
    def log_message(self, message):
        if 'WARNING' in message:
            message = utils.orange_text(message)

        self.moveCursor(QTextCursor.End)
        self.insertHtml(message.replace('\n', '<br>'))

    def clean_up(self):
        self.messages.put(ExitFlag())
        self.update_thread.wait()

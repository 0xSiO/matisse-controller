from queue import Queue

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QTextEdit

from gui import utils
from gui.threading import LoggingThread, ExitFlag


class LoggingArea(QTextEdit):
    """
    A QTextEdit that can append HTML messages to the end of the text area. Messages that contain the word
    'WARNING' will be colored.

    On initialization, a LoggingThread is started, which emits messages from a queue. Emitted messages from this thread
    are logged to the text area via a Qt slot, which runs in the creating thread for instances of this class.
    """

    def __init__(self, messages: Queue, *args, **kwargs):
        """
        Initialize an instance of LoggingArea.

        :param messages: a message queue. Messages pushed to this queue will be emitted from the LoggingThread and then
        appended to the text area.
        :param args: args to pass to QTextEdit.__init__
        :param kwargs: kwargs to pass to QTextEdit.__init__
        """

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

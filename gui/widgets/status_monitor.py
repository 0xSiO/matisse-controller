from queue import Queue

from PyQt5.QtWidgets import QLabel

from gui.threading import StatusUpdateThread, ExitFlag


class StatusMonitor(QLabel):
    """
    A QLabel that runs a StatusUpdateThread, and sets its own text to the emitted results of that thread. Each update
    executes in the creating thread for instances of this class.
    """

    def __init__(self, matisse, messages: Queue, *args, **kwargs):
        """
        Initialize an instance of StatusMonitor.

        :param matisse: an instance of Matisse to be provided to the StatusUpdateThread
        :type matisse: matisse.Matisse
        :param messages: a message queue to be given to the StatusUpdateThread
        :param args: args to pass to QLabel.__init__
        :param kwargs: kwargs to pass to QLabel.__init__
        """
        super().__init__(*args, **kwargs)
        self.messages = messages
        self.update_thread = StatusUpdateThread(matisse, messages, parent=self)
        self.update_thread.status_read.connect(self.setText)
        self.update_thread.start()

    def clean_up(self):
        self.messages.put(ExitFlag())
        self.update_thread.wait()

from contextlib import redirect_stdout

from PyQt5.QtWidgets import QApplication

from gui import Gui

app = QApplication([])
gui = Gui()
with redirect_stdout(gui.log_stream):
    app.exec()

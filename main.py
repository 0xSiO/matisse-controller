from contextlib import redirect_stdout

from gui import ControlApplication

gui = ControlApplication([])
with redirect_stdout(gui.log_stream):
    gui.exec()

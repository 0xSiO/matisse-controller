from contextlib import redirect_stdout

from gui import ControlApplication

exit_code = ControlApplication.EXIT_CODE_RESTART
while exit_code == ControlApplication.EXIT_CODE_RESTART:
    gui = ControlApplication([])
    with redirect_stdout(gui.log_stream):
        exit_code = gui.exec()
    del gui

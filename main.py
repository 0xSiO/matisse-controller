from contextlib import redirect_stdout

from gui import ControlApplication
from gui.logging import LoggingExitFlag

exit_code = ControlApplication.EXIT_CODE_REBOOT
while exit_code == ControlApplication.EXIT_CODE_REBOOT:
    gui = ControlApplication([])
    with redirect_stdout(gui.log_stream):
        exit_code = gui.exec()
        gui.log_queue.put(LoggingExitFlag())
    del gui

import sys
from contextlib import redirect_stdout

from gui import ControlApplication

# TODO: Assert that the user has provided these values
sys.argv.append('USB0::0x17E7::0x0102::07-40-01::INSTR')
sys.argv.append('COM5')
print(sys.argv)

exit_code = ControlApplication.EXIT_CODE_RESTART
while exit_code == ControlApplication.EXIT_CODE_RESTART:
    gui = ControlApplication([])
    with redirect_stdout(gui.log_stream):
        exit_code = gui.exec()
    del gui

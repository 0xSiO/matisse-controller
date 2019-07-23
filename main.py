import sys

from gui import ControlApplication

# TODO: Assert that the user has provided these values
# TODO: This instrument name is constant across our computers
sys.argv.append('USB0::0x17E7::0x0102::07-40-01::INSTR')
sys.argv.append('COM5')
print(sys.argv)

exit_code = ControlApplication.EXIT_CODE_RESTART
while exit_code == ControlApplication.EXIT_CODE_RESTART:
    gui = ControlApplication([])
    exit_code = gui.exec()
    del gui

from gui import ControlApplication


def main():
    exit_code = ControlApplication.EXIT_CODE_RESTART
    while exit_code == ControlApplication.EXIT_CODE_RESTART:
        gui = ControlApplication([])
        exit_code = gui.exec()
        del gui


if __name__ == '__main__':
    main()

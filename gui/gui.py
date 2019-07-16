from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget, QTextEdit


class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_menus()

        console_area = QTextEdit()
        console_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(console_area)

        container = QWidget()
        container.setLayout(layout)
        self.setWindowTitle('Matisse Controller')
        self.setCentralWidget(container)
        self.resize(600, 200)
        self.show()

    def setup_menus(self):
        menu_bar = self.menuBar()

        set_menu = menu_bar.addMenu('Set')
        self.set_wavelength_action = set_menu.addAction('Wavelength')
        self.set_bifi_motor_pos_action = set_menu.addAction('BiFi Motor Position')
        self.set_thin_eta_motor_pos_action = set_menu.addAction('Thin Etalon Motor Position')

        scan_menu = menu_bar.addMenu('Scan')
        self.bifi_scan_action = scan_menu.addAction('Birefringent Filter')
        self.thin_eta_scan_action = scan_menu.addAction('Thin Etalon')

        lock_menu = menu_bar.addMenu('Lock')
        self.lock_all_action = lock_all_action = lock_menu.addAction('Lock All')
        lock_all_action.setCheckable(True)
        lock_all_action.toggled.connect(self.lock_all)
        self.lock_slow_piezo_action = lock_slow_piezo_action = lock_menu.addAction('Lock Slow Piezo')
        lock_slow_piezo_action.setCheckable(True)
        self.lock_thin_etalon_action = lock_thin_etalon_action = lock_menu.addAction('Lock Thin Etalon')
        lock_thin_etalon_action.setCheckable(True)
        self.lock_piezo_etalon_action = lock_piezo_etalon_action = lock_menu.addAction('Lock Piezo Etalon')
        lock_piezo_etalon_action.setCheckable(True)
        self.lock_fast_piezo_action = lock_fast_piezo_action = lock_menu.addAction('Lock Fast Piezo')
        lock_fast_piezo_action.setCheckable(True)

    def lock_all(self, lock):
        if lock:
            for action in [self.lock_slow_piezo_action, self.lock_thin_etalon_action, self.lock_piezo_etalon_action,
                           self.lock_fast_piezo_action]:
                action.setChecked(True)
                action.setEnabled(False)
        else:
            for action in [self.lock_slow_piezo_action, self.lock_thin_etalon_action, self.lock_piezo_etalon_action,
                           self.lock_fast_piezo_action]:
                action.setChecked(False)
                action.setEnabled(True)


if __name__ == '__main__':
    app = QApplication([])
    gui = Gui()
    app.exec()

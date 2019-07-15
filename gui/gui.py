from PyQt5.QtWidgets import QApplication, QVBoxLayout, QMainWindow, QWidget, QTextEdit, QMenu, QAction


class Gui(QApplication):
    def __init__(self):
        super().__init__([])
        main_window = QMainWindow()
        layout = QVBoxLayout()
        console_area = QTextEdit()

        main_window.setWindowTitle('Matisse Controller')

        set_menu = QMenu('Set')
        set_wavelength_action = QAction('Wavelength')
        set_bifi_motor_pos_action = QAction('BiFi Motor Position')
        set_thin_eta_motor_pos_action = QAction('Thin Etalon Motor Position')
        set_menu.addActions([set_wavelength_action, set_bifi_motor_pos_action,
                             set_thin_eta_motor_pos_action])

        scan_menu = QMenu('Scan')
        bifi_scan_action = QAction('Birefringent Filter')
        thin_eta_scan_action = QAction('Thin Etalon')
        scan_menu.addActions([bifi_scan_action, thin_eta_scan_action])

        lock_menu = QMenu('Lock')
        lock_action = QAction('Set Locked?')
        lock_action.setCheckable(True)
        lock_action.toggled.connect(lambda lock: print(lock))
        lock_menu.addActions([lock_action])

        menu_bar = main_window.menuBar()
        menu_bar.addMenu(set_menu)
        menu_bar.addMenu(scan_menu)
        menu_bar.addMenu(lock_menu)

        console_area.setReadOnly(True)

        layout.addWidget(console_area)

        container = QWidget()
        container.setLayout(layout)
        main_window.setCentralWidget(container)
        main_window.resize(600, 200)
        main_window.show()
        self.exec()


Gui()

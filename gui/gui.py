import os
import subprocess
import sys
import traceback

from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QWidget, QTextEdit, QInputDialog, QMessageBox

from matisse import Matisse
from .handled_function import handled_function


# TODO: Splash screen?
class Gui(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setup_menus()
        self.setup_action_listeners()
        self.lock_actions = [self.lock_slow_piezo_action, self.lock_thin_etalon_action, self.lock_piezo_etalon_action,
                             self.lock_fast_piezo_action]

        self.log_area = log_area = QTextEdit()
        log_area.setReadOnly(True)

        layout = QVBoxLayout()
        layout.addWidget(log_area)

        container = QWidget()
        container.setLayout(layout)
        self.setWindowTitle('Matisse Controller')
        self.setCentralWidget(container)
        self.resize(600, 200)
        self.show()
        self.setup_matisse()

    def setup_menus(self):
        menu_bar = self.menuBar()

        console_menu = menu_bar.addMenu('Console')
        self.clear_log_area_action = console_menu.addAction('Clear Log')
        self.open_idle_action = console_menu.addAction('Open Python Shell...')

        set_menu = menu_bar.addMenu('Set')
        self.set_wavelength_action = set_menu.addAction('Wavelength')
        self.set_bifi_motor_pos_action = set_menu.addAction('BiFi Motor Position')
        self.set_thin_eta_motor_pos_action = set_menu.addAction('Thin Etalon Motor Position')

        scan_menu = menu_bar.addMenu('Scan')
        self.bifi_scan_action = scan_menu.addAction('Birefringent Filter')
        self.thin_eta_scan_action = scan_menu.addAction('Thin Etalon')

        lock_menu = menu_bar.addMenu('Lock')
        self.lock_all_action = lock_menu.addAction('Lock All')
        self.lock_all_action.setCheckable(True)
        self.lock_slow_piezo_action = lock_menu.addAction('Lock Slow Piezo')
        self.lock_slow_piezo_action.setCheckable(True)
        self.lock_thin_etalon_action = lock_menu.addAction('Lock Thin Etalon')
        self.lock_thin_etalon_action.setCheckable(True)
        self.lock_piezo_etalon_action = lock_menu.addAction('Lock Piezo Etalon')
        self.lock_piezo_etalon_action.setCheckable(True)
        self.lock_fast_piezo_action = lock_menu.addAction('Lock Fast Piezo')
        self.lock_fast_piezo_action.setCheckable(True)

    def setup_action_listeners(self):
        # Console
        self.clear_log_area_action.triggered.connect(self.clear_log_area)
        self.open_idle_action.triggered.connect(self.open_idle)

        # Set
        self.set_wavelength_action.triggered.connect(self.set_wavelength_dialog)
        self.set_bifi_motor_pos_action.triggered.connect(self.set_bifi_motor_pos_dialog)
        self.set_thin_eta_motor_pos_action.triggered.connect(self.set_thin_eta_motor_pos_dialog)

        # Scan
        self.bifi_scan_action.triggered.connect(self.start_bifi_scan)
        self.thin_eta_scan_action.triggered.connect(self.start_thin_etalon_scan)

        # Lock
        self.lock_all_action.triggered.connect(self.toggle_lock_all)
        self.lock_slow_piezo_action.triggered.connect(self.toggle_slow_piezo_lock)
        self.lock_thin_etalon_action.triggered.connect(self.toggle_thin_etalon_lock)
        self.lock_piezo_etalon_action.triggered.connect(self.toggle_piezo_etalon_lock)
        self.lock_fast_piezo_action.triggered.connect(self.toggle_fast_piezo_lock)

    @handled_function
    def setup_matisse(self):
        # TODO: Initialize Matisse
        self.matisse: Matisse = None

    # TODO: For logging, use a Queue. https://stackoverflow.com/questions/21071448/redirecting-stdout-and-stderr-to-a-pyqt4-qtextedit-from-a-secondary-thread
    def log(self, message, end='\n'):
        self.log_area.setText(self.log_area.toPlainText() + message + end)

    def error_dialog(self):
        stack = list(traceback.format_exception(*sys.exc_info()))
        # Pick length of longest line in stack, with a cutoff at 185
        desired_width = min(max([len(line) for line in stack]), 185)
        description = stack.pop()
        self.log(description, end='')
        # Remove entries for handled_function decorator, for clarity
        stack = filter(lambda item: os.path.join('gui', 'handled_function.py') not in item, stack)
        dialog = QMessageBox(icon=QMessageBox.Critical)
        dialog.setWindowTitle('Error')
        # Adding the underscores is a hack to resize the QMessageBox because it's not normally resizable.
        # This looks good in Windows, haven't tested other platforms. Sorry :(
        dialog.setText(f"{description + '_' * desired_width}\n\n{''.join(stack)}")
        dialog.exec()

    @handled_function
    def clear_log_area(self, checked):
        self.log_area.clear()

    @handled_function
    def open_idle(self, checked):
        self.log('Opening IDLE.')
        subprocess.Popen('python -m idlelib -t "Matisse Controller - Python Shell" -c "from matisse import Matisse; ' +
                         'matisse = Matisse(); print(\'Access the Matisse using \\\'matisse.[method]\\\'\')"')

    @handled_function
    def set_wavelength_dialog(self, checked):
        # TODO: Set default value to current target wavelength or just to the middle
        target_wavelength, success = QInputDialog.getDouble(self, 'Set Wavelength', 'Wavelength (nm): ')
        if success:
            self.log(f"Setting wavelength to {target_wavelength} nm...")

    @handled_function
    def set_bifi_motor_pos_dialog(self, checked):
        # TODO: Set default value to current position or just to the middle
        target_position, success = QInputDialog.getInt(self, 'Set BiFi Motor Position', 'Absolute Position:')
        if success:
            self.log(f"Setting BiFi motor position to {target_position}.")

    @handled_function
    def set_thin_eta_motor_pos_dialog(self, checked):
        # TODO: Set default value to current position or just to the middle
        target_position, success = QInputDialog.getInt(self, 'Set Thin Etalon Motor Position', 'Absolute Position:')
        if success:
            self.log(f"Setting thin etalon motor position to {target_position}.")

    @handled_function
    def start_bifi_scan(self, checked):
        self.log("Starting BiFi scan...")

    @handled_function
    def start_thin_etalon_scan(self, checked):
        self.log("Starting thin etalon scan...")

    @handled_function
    def toggle_lock_all(self, checked):
        if checked:
            for action in self.lock_actions:
                if not action.isChecked():
                    action.trigger()
            if all([action.isChecked() for action in self.lock_actions]):
                [action.setEnabled(False) for action in self.lock_actions]
            else:
                self.lock_all_action.setChecked(False)
                self.log("Couldn't lock all laser components.")
        else:
            for action in reversed(self.lock_actions):
                action.trigger()
                action.setEnabled(True)

    @handled_function
    def toggle_slow_piezo_lock(self, checked):
        self.log(f"{'Locking' if checked else 'Unlocking'} slow piezo.")
        raise NotImplementedError

    @handled_function
    def toggle_thin_etalon_lock(self, checked):
        self.log(f"{'Locking' if checked else 'Unlocking'} thin etalon.")
        raise NotImplementedError

    @handled_function
    def toggle_piezo_etalon_lock(self, checked):
        self.log(f"{'Locking' if checked else 'Unlocking'} piezo etalon.")
        raise NotImplementedError

    @handled_function
    def toggle_fast_piezo_lock(self, checked):
        self.log(f"{'Locking' if checked else 'Unlocking'} fast piezo.")
        raise NotImplementedError

import queue
import sys
import traceback
from concurrent.futures import Future
from concurrent.futures.thread import ThreadPoolExecutor
from contextlib import redirect_stdout

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QVBoxLayout, QMainWindow, QWidget, QInputDialog, QMessageBox, QApplication

import matisse_controller.config as cfg
from matisse_controller.gui import utils
from matisse_controller.gui.dialogs import ConfigurationDialog
from matisse_controller.gui.logging_stream import LoggingStream
from matisse_controller.gui.utils import handled_function, handled_slot
from matisse_controller.gui.widgets import LoggingArea, StatusMonitor
from matisse_controller.matisse import Matisse


class ControlApplication(QApplication):
    EXIT_CODE_RESTART = 42  # Answer to the Ultimate Question of Life, the Universe, and Everything
    CONFIRM_WAVELENGTH_CHANGE_THRESHOLD = 10

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Non-handled functions only here
        self.setup_window()
        self.setup_logging()
        self.setup_menus()
        self.setup_slots()

        # Handled functions can go here
        self.setup_matisse()
        self.setup_widgets()

        # Other setup
        self.aboutToQuit.connect(self.clean_up)
        self.work_executor = ThreadPoolExecutor()
        self.matisse_worker: Future = None

        container = QWidget()
        container.setLayout(self.layout)
        self.window.setCentralWidget(container)
        self.window.show()

    def setup_window(self):
        self.window = window = QMainWindow()
        self.layout = QVBoxLayout()
        window.setWindowTitle('Matisse Controller')
        window.resize(600, 300)

    def setup_logging(self):
        self.log_queue = queue.Queue()
        self.log_area = LoggingArea(self.log_queue)
        self.log_area.setReadOnly(True)
        self.layout.addWidget(self.log_area)

        # Set up a context manager to redirect stdout to the log window
        self.log_redirector = redirect_stdout(LoggingStream(self.log_queue))
        self.log_redirector.__enter__()

    def setup_menus(self):
        menu_bar = self.window.menuBar()

        console_menu = menu_bar.addMenu('Console')
        self.clear_log_area_action = console_menu.addAction('Clear Log')
        self.configuration_action = console_menu.addAction('Configuration')
        self.reset_action = console_menu.addAction('Reset')
        self.restart_action = console_menu.addAction('Restart')

        set_menu = menu_bar.addMenu('Set')
        self.set_wavelength_action = set_menu.addAction('Wavelength')
        self.set_bifi_approx_wavelength_action = set_menu.addAction('BiFi Approx. Wavelength')
        self.set_bifi_motor_pos_action = set_menu.addAction('BiFi Motor Position')
        self.set_thin_eta_motor_pos_action = set_menu.addAction('Thin Etalon Motor Position')
        self.set_piezo_eta_pos_action = set_menu.addAction('Piezo Etalon Position')
        self.set_slow_piezo_pos_action = set_menu.addAction('Slow Piezo Position')
        self.set_refcell_pos_action = set_menu.addAction('RefCell Position')

        scan_menu = menu_bar.addMenu('Scan')
        self.bifi_scan_action = scan_menu.addAction('Birefringent Filter')
        self.thin_eta_scan_action = scan_menu.addAction('Thin Etalon')

        ple_menu = menu_bar.addMenu('PLE')
        self.scan_device_up_action = ple_menu.addAction('Scan Up')
        self.scan_device_down_action = ple_menu.addAction('Scan Down')
        self.stop_scan_device_action = ple_menu.addAction('Stop Scanning')

        stabilization_menu = menu_bar.addMenu('Stabilization')
        toggle_control_loop_menu = stabilization_menu.addMenu('Toggle Control Loop')
        self.slow_pz_control_action = toggle_control_loop_menu.addAction('Slow Piezo')
        self.slow_pz_control_action.setCheckable(True)
        self.thin_eta_control_action = toggle_control_loop_menu.addAction('Thin Etalon')
        self.thin_eta_control_action.setCheckable(True)
        self.piezo_eta_control_action = toggle_control_loop_menu.addAction('Piezo Etalon')
        self.piezo_eta_control_action.setCheckable(True)
        self.fast_pz_control_action = toggle_control_loop_menu.addAction('Fast Piezo')
        self.fast_pz_control_action.setCheckable(True)
        self.lock_laser_action = stabilization_menu.addAction('Toggle Lock Laser')
        self.auto_stabilize_action = stabilization_menu.addAction('Toggle Auto Stabilization')

        self.control_loop_actions = [self.slow_pz_control_action, self.thin_eta_control_action,
                                     self.piezo_eta_control_action, self.fast_pz_control_action]

    def setup_slots(self):
        # Console
        self.clear_log_area_action.triggered.connect(self.clear_log_area)
        self.configuration_action.triggered.connect(self.open_configuration)
        self.reset_action.triggered.connect(self.reset_matisse)
        self.restart_action.triggered.connect(self.restart)

        # Set
        self.set_wavelength_action.triggered.connect(self.set_wavelength_dialog)
        self.set_bifi_approx_wavelength_action.triggered.connect(self.set_bifi_approx_wavelength_dialog)
        self.set_bifi_motor_pos_action.triggered.connect(self.set_bifi_motor_pos_dialog)
        self.set_thin_eta_motor_pos_action.triggered.connect(self.set_thin_eta_motor_pos_dialog)
        self.set_piezo_eta_pos_action.triggered.connect(self.set_piezo_eta_pos_dialog)
        self.set_slow_piezo_pos_action.triggered.connect(self.set_slow_piezo_pos_dialog)
        self.set_refcell_pos_action.triggered.connect(self.set_refcell_pos_dialog)

        # Scan
        self.bifi_scan_action.triggered.connect(self.start_bifi_scan)
        self.thin_eta_scan_action.triggered.connect(self.start_thin_etalon_scan)

        # PLE
        self.scan_device_up_action.triggered.connect(self.scan_device_up)
        self.scan_device_down_action.triggered.connect(self.scan_device_down)
        self.stop_scan_device_action.triggered.connect(self.stop_scanning_device)

        # Stabilization
        self.lock_laser_action.triggered.connect(self.toggle_lock_laser)
        self.slow_pz_control_action.triggered.connect(self.toggle_slow_piezo_control)
        self.thin_eta_control_action.triggered.connect(self.toggle_thin_etalon_control)
        self.piezo_eta_control_action.triggered.connect(self.toggle_piezo_etalon_control)
        self.fast_pz_control_action.triggered.connect(self.toggle_fast_piezo_control)
        self.auto_stabilize_action.triggered.connect(self.toggle_auto_stabilization)

    @handled_function
    def setup_widgets(self):
        self.status_monitor_queue = queue.Queue()
        self.status_monitor = StatusMonitor(self.matisse, self.status_monitor_queue)
        self.layout.addWidget(self.status_monitor)

    @handled_function
    def setup_matisse(self):
        try:
            self.matisse: Matisse = Matisse()
        except Exception as err:
            self.matisse: Matisse = None
            raise err

    @pyqtSlot()
    def clean_up(self):
        self.reset_matisse()

        # Clean up widgets with running threads.
        self.status_monitor.clean_up()
        self.log_area.clean_up()

        self.log_redirector.__exit__(None, None, None)

    def error_dialog(self):
        stack = list(traceback.format_exception(*sys.exc_info()))
        # Pick length of longest line in stack, with a cutoff at 185
        desired_width = min(max([len(line) for line in stack]), 185)
        description = stack.pop()
        print(utils.red_text(description), end='')
        # Remove entries for handled_function decorator, for clarity
        stack = filter(lambda item: 'in handled_function_wrapper' not in item, stack)
        dialog = QMessageBox(icon=QMessageBox.Critical)
        dialog.setWindowTitle('Error')
        # Adding the underscores is a hack to resize the QMessageBox because it's not normally resizable.
        # This looks good in Windows, haven't tested other platforms. Sorry :(
        dialog.setText(f"{description + '_' * desired_width}\n\n{''.join(stack)}")
        dialog.exec()

    @handled_slot(bool)
    def clear_log_area(self, checked):
        self.log_area.clear()

    @handled_slot(bool)
    def open_configuration(self, checked):
        dialog = ConfigurationDialog()
        dialog.exec()

    @handled_slot(bool)
    def reset_matisse(self, checked=False):
        """Reset Matisse to a 'good' default state."""
        print('Starting reset.')
        if self.matisse is not None:
            self.matisse.exit_flag = True
            if self.matisse_worker is not None and self.matisse_worker.running():
                print('Waiting for running tasks to complete.')
                self.matisse_worker.result()
            self.matisse_worker = None
            self.matisse.stabilize_off()
            self.matisse.stop_laser_lock_correction()
            self.matisse.exit_flag = False
        print('Reset complete.')

    @handled_slot(bool)
    def restart(self, checked):
        # TODO: Check if clean_up is called here
        self.exit(ControlApplication.EXIT_CODE_RESTART)

    @handled_slot(bool)
    def set_wavelength_dialog(self, checked):
        current_wavelength = self.matisse.target_wavelength
        if current_wavelength is None:
            current_wavelength = self.matisse.wavemeter_wavelength()
        # TODO: Set min and max to reasonable values
        target_wavelength, success = QInputDialog.getDouble(self.window, 'Set Wavelength', 'Wavelength (nm): ',
                                                            current_wavelength, decimals=3)
        if success:
            if abs(current_wavelength - target_wavelength) >= ControlApplication.CONFIRM_WAVELENGTH_CHANGE_THRESHOLD:
                answer = QMessageBox.warning(self.window, 'Large Wavelength Change',
                                             f"The desired wavelength, {target_wavelength} nm, is more than "
                                             f"{ControlApplication.CONFIRM_WAVELENGTH_CHANGE_THRESHOLD} nm "
                                             'away from the current wavelength. Are you sure?',
                                             QMessageBox.Yes | QMessageBox.No, defaultButton=QMessageBox.No)
                if answer == QMessageBox.No:
                    return

            print(f"Setting wavelength to {target_wavelength} nm...")
            self.run_matisse_task(self.matisse.set_wavelength, target_wavelength)

    @handled_slot(bool)
    def set_bifi_approx_wavelength_dialog(self, checked):
        target_wavelength, success = QInputDialog.getDouble(self.window, 'Set Approx. Wavelength', 'Wavelength (nm): ',
                                                            self.matisse.query('MOTBI:WL?', numeric_result=True))
        if success:
            print(f"Setting BiFi approximate wavelength to {target_wavelength} nm...")
            self.matisse.set_bifi_wavelength(target_wavelength)

    @handled_slot(bool)
    def set_bifi_motor_pos_dialog(self, checked):
        target_pos, success = QInputDialog.getInt(self.window, 'Set BiFi Motor Position', 'Absolute Position:',
                                                  self.matisse.query('MOTBI:POS?', numeric_result=True))
        if success:
            print(f"Setting BiFi motor position to {target_pos}.")
            self.matisse.set_bifi_motor_pos(target_pos)

    @handled_slot(bool)
    def set_thin_eta_motor_pos_dialog(self, checked):
        target_pos, success = QInputDialog.getInt(self.window, 'Set Thin Etalon Motor Position', 'Absolute Position:',
                                                  self.matisse.query('MOTTE:POS?', numeric_result=True))
        if success:
            print(f"Setting thin etalon motor position to {target_pos}.")
            self.matisse.set_thin_etalon_motor_pos(target_pos)

    @handled_slot(bool)
    def set_piezo_eta_pos_dialog(self, checked):
        target_pos, success = QInputDialog.getDouble(self.window, 'Set Piezo Etalon Position', 'Position: ',
                                                     self.matisse.query('PZETL:BASE?', numeric_result=True))
        if success:
            self.matisse.query(f"PZETL:BASE {target_pos}")

    @handled_slot(bool)
    def set_slow_piezo_pos_dialog(self, checked):
        target_pos, success = QInputDialog.getDouble(self.window, 'Set Slow Piezo Position', 'Position: ',
                                                     self.matisse.query('SPZT:NOW?', numeric_result=True))
        if success:
            self.matisse.query(f"SPZT:NOW {target_pos}")

    @handled_slot(bool)
    def set_refcell_pos_dialog(self, checked):
        target_pos, success = QInputDialog.getDouble(self.window, 'Set RefCell Position', 'Position: ',
                                                     self.matisse.query('SCAN:NOW?', numeric_result=True))
        if success:
            self.matisse.query(f"SCAN:NOW {target_pos}")

    @handled_slot(bool)
    def start_bifi_scan(self, checked):
        self.run_matisse_task(self.matisse.birefringent_filter_scan)

    @handled_slot(bool)
    def start_thin_etalon_scan(self, checked):
        self.run_matisse_task(self.matisse.thin_etalon_scan)

    @handled_slot(bool)
    def scan_device_up(self, checked):
        if self.matisse.is_stabilizing():
            print('WARNING: Auto-stabilize is on. Disable it and try again.')
        else:
            self._matisse.query(f"SCAN:RISINGSPEED {cfg.get(cfg.REFCELL_SCAN_RISING_SPEED)}")
            self._matisse.query(f"SCAN:FALLINGSPEED {cfg.get(cfg.REFCELL_SCAN_FALLING_SPEED)}")
            self.matisse.start_scan(Matisse.SCAN_MODE_UP)

    @handled_slot(bool)
    def scan_device_down(self, checked):
        if self.matisse.is_stabilizing():
            print('WARNING: Auto-stabilize is on. Disable it and try again.')
        else:
            self._matisse.query(f"SCAN:RISINGSPEED {cfg.get(cfg.REFCELL_SCAN_RISING_SPEED)}")
            self._matisse.query(f"SCAN:FALLINGSPEED {cfg.get(cfg.REFCELL_SCAN_FALLING_SPEED)}")
            self.matisse.start_scan(Matisse.SCAN_MODE_DOWN)

    @handled_slot(bool)
    def stop_scanning_device(self, checked):
        if self.matisse.is_stabilizing():
            print('WARNING: Auto-stabilize is on. Disable it and try again.')
        else:
            self.matisse.stop_scan()

    @handled_slot(bool)
    def toggle_lock_laser(self, checked):
        if self.matisse.is_lock_correction_on():
            self.matisse.stop_laser_lock_correction()
            [action.setEnabled(True) for action in self.control_loop_actions]
            [action.setChecked(False) for action in self.control_loop_actions]
        else:
            self.matisse.start_laser_lock_correction()
            [action.setEnabled(False) for action in self.control_loop_actions]
            [action.setChecked(True) for action in self.control_loop_actions]

    @handled_slot(bool)
    def toggle_slow_piezo_control(self, checked):
        print(f"{'Locking' if checked else 'Unlocking'} slow piezo.")
        self.slow_pz_control_action.setChecked(not checked)
        self.matisse.set_slow_piezo_control(checked)
        self.slow_pz_control_action.setChecked(checked)

    @handled_slot(bool)
    def toggle_thin_etalon_control(self, checked):
        print(f"{'Locking' if checked else 'Unlocking'} thin etalon.")
        self.thin_eta_control_action.setChecked(not checked)
        self.matisse.set_thin_etalon_control(checked)
        self.thin_eta_control_action.setChecked(checked)

    @handled_slot(bool)
    def toggle_piezo_etalon_control(self, checked):
        print(f"{'Locking' if checked else 'Unlocking'} piezo etalon.")
        self.piezo_eta_control_action.setChecked(not checked)
        self.matisse.set_piezo_etalon_control(checked)
        self.piezo_eta_control_action.setChecked(checked)

    @handled_slot(bool)
    def toggle_fast_piezo_control(self, checked):
        print(f"{'Locking' if checked else 'Unlocking'} fast piezo.")
        self.fast_pz_control_action.setChecked(not checked)
        self.matisse.set_piezo_etalon_control(checked)
        self.fast_pz_control_action.setChecked(checked)

    @handled_slot(bool)
    def toggle_auto_stabilization(self, checked):
        if self.matisse.is_stabilizing():
            self.matisse.stabilize_off()
        else:
            self.matisse.stabilize_on()

    def run_matisse_task(self, function, *args, **kwargs) -> bool:
        """
        Run an asynchronous Matisse-related task in the worker thread pool. Only one such task may be run at a time.
        Any task run using this method MUST exit gracefully at some point by checking the Matisse exit_flag.

        :param function: the function to run in the thread pool
        :param args: positional arguments to pass to the given function
        :param kwargs: keyword arguments to pass to the given function
        :return: whether the task was successfully started
        """
        if self.matisse_worker is not None and self.matisse_worker.running():
            print("WARNING: Cannot perform requested action. A Matisse-related task is currently running.")
            return False
        else:
            self.matisse_worker = self.work_executor.submit(function, *args, **kwargs)
            self.matisse_worker.add_done_callback(self.raise_error_from_future)
            return True

    @handled_function
    def raise_error_from_future(self, future: Future):
        async_task_error = future.exception()
        if async_task_error is not None:
            raise async_task_error


def main():
    exit_code = ControlApplication.EXIT_CODE_RESTART
    while exit_code == ControlApplication.EXIT_CODE_RESTART:
        gui = ControlApplication([])
        exit_code = gui.exec()
        del gui


if __name__ == '__main__':
    main()

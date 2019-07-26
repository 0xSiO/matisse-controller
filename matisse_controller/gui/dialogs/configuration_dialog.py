from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *

import matisse_controller.config as cfg
from matisse_controller.matisse import Matisse


class ConfigurationDialog(QDialog):
    """A dialog for displaying and modifying selected configurable options that affect the behavior of the program."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Configuration')
        self.resize(700, 200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.add_options()
        self.set_current_values_from_config()
        self.add_buttons()

    # TODO: Tooltips
    def add_options(self):
        scan_options = self.create_scan_options()
        locking_options = self.create_locking_options()

        form = QWidget()
        form_layout = QHBoxLayout()
        form.setLayout(form_layout)
        form_layout.addWidget(scan_options)
        form_layout.addWidget(locking_options)
        self.layout.addWidget(form)

    def create_scan_options(self):
        scan_options = QGroupBox('Scanning')
        scan_layout = QFormLayout()
        scan_options.setLayout(scan_layout)
        self.bifi_scan_range_field = QSpinBox()
        self.bifi_scan_range_field.setMaximum(Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT / 2)
        scan_layout.addRow('BiFi normal scan range:', self.bifi_scan_range_field)
        self.bifi_small_scan_range_field = QSpinBox()
        self.bifi_small_scan_range_field.setMaximum(Matisse.BIREFRINGENT_FILTER_UPPER_LIMIT / 4)
        scan_layout.addRow('BiFi small scan range:', self.bifi_small_scan_range_field)
        self.bifi_scan_step_field = QSpinBox()
        scan_layout.addRow('BiFi scan step:', self.bifi_scan_step_field)
        self.thin_eta_scan_range_field = QSpinBox()
        self.thin_eta_scan_range_field.setMaximum(Matisse.THIN_ETALON_UPPER_LIMIT / 2)
        scan_layout.addRow('Thin etalon normal scan range:', self.thin_eta_scan_range_field)
        self.thin_eta_small_scan_range_field = QSpinBox()
        self.thin_eta_small_scan_range_field.setMaximum(Matisse.THIN_ETALON_UPPER_LIMIT / 4)
        scan_layout.addRow('Thin etalon small scan range:', self.thin_eta_small_scan_range_field)
        self.thin_eta_scan_step_field = QSpinBox()
        scan_layout.addRow('Thin etalon scan step:', self.thin_eta_scan_step_field)
        self.thin_eta_nudge_field = QSpinBox()
        scan_layout.addRow('Thin etalon scan nudge:', self.thin_eta_nudge_field)
        self.refcell_rising_speed_field = QDoubleSpinBox()
        self.refcell_rising_speed_field.setDecimals(3)
        self.refcell_rising_speed_field.setSingleStep(0.001)
        self.refcell_rising_speed_field.setMinimum(0)
        self.refcell_rising_speed_field.setMaximum(0.1)
        scan_layout.addRow('RefCell scan rising speed: ', self.refcell_rising_speed_field)
        self.refcell_falling_speed_field = QDoubleSpinBox()
        self.refcell_falling_speed_field.setDecimals(3)
        self.refcell_falling_speed_field.setSingleStep(0.001)
        self.refcell_falling_speed_field.setMinimum(0)
        self.refcell_falling_speed_field.setMaximum(0.1)
        scan_layout.addRow('RefCell scan falling speed: ', self.refcell_falling_speed_field)
        self.large_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Large wavelength drift: ', self.large_wavelength_drift_field)
        self.medium_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Medium wavelength drift: ', self.medium_wavelength_drift_field)
        self.small_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Small wavelength drift: ', self.small_wavelength_drift_field)
        return scan_options

    def create_locking_options(self):
        locking_options = QGroupBox('Locking/Stabilization')
        locking_layout = QFormLayout()
        locking_options.setLayout(locking_layout)
        self.locking_timeout_field = QDoubleSpinBox()
        self.locking_timeout_field.setMinimum(0)
        locking_layout.addRow('Locking timeout: ', self.locking_timeout_field)
        self.pz_eta_correction_pos_field = QDoubleSpinBox()
        self.pz_eta_correction_pos_field.setMinimum(Matisse.PIEZO_ETALON_LOWER_LIMIT)
        self.pz_eta_correction_pos_field.setMaximum(Matisse.PIEZO_ETALON_UPPER_LIMIT)
        locking_layout.addRow('Piezo etalon correction pos: ', self.pz_eta_correction_pos_field)
        self.slow_pz_correction_pos_field = QDoubleSpinBox()
        self.slow_pz_correction_pos_field.setMinimum(Matisse.SLOW_PIEZO_LOWER_LIMIT)
        self.slow_pz_correction_pos_field.setMaximum(Matisse.SLOW_PIEZO_UPPER_LIMIT)
        locking_layout.addRow('Slow piezo correction pos: ', self.slow_pz_correction_pos_field)
        self.refcell_correction_pos_field = QDoubleSpinBox()
        self.refcell_correction_pos_field.setMinimum(Matisse.REFERENCE_CELL_LOWER_LIMIT)
        self.refcell_correction_pos_field.setMaximum(Matisse.REFERENCE_CELL_UPPER_LIMIT)
        locking_layout.addRow('RefCell correction pos: ', self.refcell_correction_pos_field)
        self.stabilization_rising_speed_field = QDoubleSpinBox()
        self.stabilization_rising_speed_field.setDecimals(3)
        self.stabilization_rising_speed_field.setSingleStep(0.001)
        self.stabilization_rising_speed_field.setMinimum(0)
        self.stabilization_rising_speed_field.setMaximum(0.1)
        locking_layout.addRow('Auto-stabilization rising speed: ', self.stabilization_rising_speed_field)
        self.stabilization_falling_speed_field = QDoubleSpinBox()
        self.stabilization_falling_speed_field.setDecimals(3)
        self.stabilization_falling_speed_field.setSingleStep(0.001)
        self.stabilization_falling_speed_field.setMinimum(0)
        self.stabilization_falling_speed_field.setMaximum(0.1)
        locking_layout.addRow('Auto-stabilization falling speed: ', self.stabilization_falling_speed_field)
        self.stabilization_delay_field = QDoubleSpinBox()
        self.stabilization_delay_field.setMinimum(0.1)
        locking_layout.addRow('Auto-stabilization delay: ', self.stabilization_delay_field)
        self.stabilization_tolerance_field = QDoubleSpinBox()
        self.stabilization_tolerance_field.setDecimals(4)
        self.stabilization_tolerance_field.setSingleStep(0.0001)
        self.stabilization_tolerance_field.setMinimum(0.0001)
        locking_layout.addRow('Auto-stabilization tolerance: ', self.stabilization_tolerance_field)
        return locking_options

    def set_current_values_from_config(self):
        self.bifi_scan_range_field.setValue(cfg.get(cfg.BIFI_SCAN_RANGE))
        self.bifi_small_scan_range_field.setValue(cfg.get(cfg.BIFI_SCAN_RANGE_SMALL))
        self.bifi_scan_step_field.setValue(cfg.get(cfg.BIFI_SCAN_STEP))

        self.thin_eta_scan_range_field.setValue(cfg.get(cfg.THIN_ETA_SCAN_RANGE))
        self.thin_eta_small_scan_range_field.setValue(cfg.get(cfg.THIN_ETA_SCAN_RANGE_SMALL))
        self.thin_eta_scan_step_field.setValue(cfg.get(cfg.THIN_ETA_SCAN_STEP))
        self.thin_eta_nudge_field.setValue(cfg.get(cfg.THIN_ETA_NUDGE))

        self.refcell_rising_speed_field.setValue(cfg.get(cfg.REFCELL_SCAN_RISING_SPEED))
        self.refcell_falling_speed_field.setValue(cfg.get(cfg.REFCELL_SCAN_FALLING_SPEED))

        self.large_wavelength_drift_field.setValue(cfg.get(cfg.LARGE_WAVELENGTH_DRIFT))
        self.medium_wavelength_drift_field.setValue(cfg.get(cfg.MEDIUM_WAVELENGTH_DRIFT))
        self.small_wavelength_drift_field.setValue(cfg.get(cfg.SMALL_WAVELENGTH_DRIFT))

        self.locking_timeout_field.setValue(cfg.get(cfg.LOCKING_TIMEOUT))

        self.pz_eta_correction_pos_field.setValue(cfg.get(cfg.PIEZO_ETA_CORRECTION_POS))
        self.slow_pz_correction_pos_field.setValue(cfg.get(cfg.SLOW_PIEZO_CORRECTION_POS))
        self.refcell_correction_pos_field.setValue(cfg.get(cfg.REFCELL_CORRECTION_POS))

        self.stabilization_rising_speed_field.setValue(cfg.get(cfg.STABILIZATION_RISING_SPEED))
        self.stabilization_falling_speed_field.setValue(cfg.get(cfg.STABILIZATION_FALLING_SPEED))
        self.stabilization_delay_field.setValue(cfg.get(cfg.STABILIZATION_DELAY))
        self.stabilization_tolerance_field.setValue(cfg.get(cfg.STABILIZATION_TOLERANCE))

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).clicked.connect(self.save_configuration)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel)
        self.layout.addWidget(button_box)

    @pyqtSlot(bool)
    def save_configuration(self, checked):
        print('Saving configuration.')
        # TODO: create separate UI section for device ID
        cfg.set(cfg.MATISSE_DEVICE_ID, 'USB0::0x17E7::0x0102::07-40-01::INSTR')

        cfg.set(cfg.BIFI_SCAN_RANGE, self.bifi_scan_range_field.value())
        cfg.set(cfg.BIFI_SCAN_RANGE_SMALL, self.bifi_small_scan_range_field.value())
        cfg.set(cfg.BIFI_SCAN_STEP, self.bifi_scan_step_field.value())

        cfg.set(cfg.THIN_ETA_SCAN_RANGE, self.thin_eta_scan_range_field.value())
        cfg.set(cfg.THIN_ETA_SCAN_RANGE_SMALL, self.thin_eta_small_scan_range_field.value())
        cfg.set(cfg.THIN_ETA_SCAN_STEP, self.thin_eta_scan_step_field.value())
        cfg.set(cfg.THIN_ETA_NUDGE, self.thin_eta_nudge_field.value())

        cfg.set(cfg.REFCELL_SCAN_RISING_SPEED, self.refcell_rising_speed_field.value())
        cfg.set(cfg.REFCELL_SCAN_FALLING_SPEED, self.refcell_falling_speed_field.value())

        cfg.set(cfg.LARGE_WAVELENGTH_DRIFT, self.large_wavelength_drift_field.value())
        cfg.set(cfg.MEDIUM_WAVELENGTH_DRIFT, self.medium_wavelength_drift_field.value())
        cfg.set(cfg.SMALL_WAVELENGTH_DRIFT, self.small_wavelength_drift_field.value())

        cfg.set(cfg.LOCKING_TIMEOUT, self.locking_timeout_field.value())

        cfg.set(cfg.PIEZO_ETA_CORRECTION_POS, self.pz_eta_correction_pos_field.value())
        cfg.set(cfg.SLOW_PIEZO_CORRECTION_POS, self.slow_pz_correction_pos_field.value())
        cfg.set(cfg.REFCELL_CORRECTION_POS, self.refcell_correction_pos_field.value())

        cfg.set(cfg.STABILIZATION_RISING_SPEED, self.stabilization_rising_speed_field.value())
        cfg.set(cfg.STABILIZATION_FALLING_SPEED, self.stabilization_falling_speed_field.value())
        cfg.set(cfg.STABILIZATION_DELAY, self.stabilization_delay_field.value())
        cfg.set(cfg.STABILIZATION_TOLERANCE, self.stabilization_tolerance_field.value())

        # TODO: wavemeter and GUI config
        cfg.set('wavemeter', {})
        cfg.set('gui', {})

        cfg.save()
        self.close()

    @pyqtSlot(bool)
    def cancel(self, checked):
        self.close()


def main():
    app = QApplication([])
    d = ConfigurationDialog()
    d.exec()
    app.exit()


if __name__ == '__main__':
    main()

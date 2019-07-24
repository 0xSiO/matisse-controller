from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *

import config as cfg
from matisse import Matisse


class ConfigurationDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Configuration')
        self.resize(700, 200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.add_options()
        self.add_buttons()
        # TODO: Load defaults
        self.config = {}

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
        scan_layout.addRow('BiFi Normal Scan Range:', self.bifi_scan_range_field)
        self.bifi_small_scan_range_field = QSpinBox()
        scan_layout.addRow('BiFi Small Scan Range:', self.bifi_small_scan_range_field)
        self.bifi_scan_step_field = QSpinBox()
        scan_layout.addRow('BiFi Scan Step:', self.bifi_scan_step_field)
        self.thin_eta_scan_range_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Normal Scan Range:', self.thin_eta_scan_range_field)
        self.thin_eta_small_scan_range_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Small Scan Range:', self.thin_eta_small_scan_range_field)
        self.thin_eta_scan_step_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Scan Step:', self.thin_eta_scan_step_field)
        self.thin_eta_nudge_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Scan Nudge:', self.thin_eta_nudge_field)
        self.large_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Large Wavelength Drift: ', self.large_wavelength_drift_field)
        self.medium_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Medium Wavelength Drift: ', self.medium_wavelength_drift_field)
        self.small_wavelength_drift_field = QDoubleSpinBox()
        scan_layout.addRow('Small Wavelength Drift: ', self.small_wavelength_drift_field)
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
        locking_layout.addRow('Piezo Etalon Correction Pos: ', self.pz_eta_correction_pos_field)
        self.slow_pz_correction_pos_field = QDoubleSpinBox()
        self.slow_pz_correction_pos_field.setMinimum(Matisse.SLOW_PIEZO_LOWER_LIMIT)
        self.slow_pz_correction_pos_field.setMaximum(Matisse.SLOW_PIEZO_UPPER_LIMIT)
        locking_layout.addRow('Slow Piezo Correction Pos: ', self.slow_pz_correction_pos_field)
        self.refcell_correction_pos_field = QDoubleSpinBox()
        self.refcell_correction_pos_field.setMinimum(Matisse.REFERENCE_CELL_LOWER_LIMIT)
        self.refcell_correction_pos_field.setMaximum(Matisse.REFERENCE_CELL_UPPER_LIMIT)
        locking_layout.addRow('RefCell Correction Pos: ', self.refcell_correction_pos_field)
        return locking_options

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).clicked.connect(self.save_configuration)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel)
        self.layout.addWidget(button_box)

    def parse_config(self):
        return {
            'matisse': {
                # TODO: create separate UI section for device ID
                'device_id': 'USB0::0x17E7::0x0102::07-40-01::INSTR',
                'scanning': {
                    'wavelength_drift': {
                        'large': self.large_wavelength_drift_field.value(),
                        'medium': self.medium_wavelength_drift_field.value(),
                        'small': self.small_wavelength_drift_field.value()
                    },
                    'birefringent_filter': {
                        'scan_range': self.bifi_scan_range_field.value(),
                        'scan_range_small': self.bifi_small_scan_range_field.value(),
                        'step': self.bifi_scan_step_field.value()
                    },
                    'thin_etalon': {
                        'scan_range': self.thin_eta_scan_range_field.value(),
                        'scan_range_small': self.thin_eta_small_scan_range_field.value(),
                        'step': self.thin_eta_scan_step_field.value(),
                        'nudge': self.thin_eta_nudge_field.value()
                    }
                },
                'locking': {
                    'timeout': self.locking_timeout_field.value()
                },
                'correction': {
                    'piezo_etalon_pos': self.pz_eta_correction_pos_field.value(),
                    'slow_piezo_pos': self.slow_pz_correction_pos_field.value(),
                    'refcell_pos': self.refcell_correction_pos_field.value()
                }
            },
            'wavemeter': {
                'port': 'COM5',
                'precision': 3
            },
            'gui': {}
        }

    @pyqtSlot(bool)
    def save_configuration(self, checked):
        print('Saving configuration.')
        new_config = self.parse_config()
        cfg.configuration.CONFIGURATION = new_config
        cfg.save()
        self.close()

    @pyqtSlot(bool)
    def cancel(self, checked):
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    d = ConfigurationDialog()
    d.exec()
    app.exit(0)

import json

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *

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
        bifi_scan_range_field = QSpinBox()
        scan_layout.addRow('BiFi Normal Scan Range:', bifi_scan_range_field)
        bifi_small_scan_range_field = QSpinBox()
        scan_layout.addRow('BiFi Small Scan Range:', bifi_small_scan_range_field)
        bifi_scan_step_field = QSpinBox()
        scan_layout.addRow('BiFi Scan Step:', bifi_scan_step_field)
        thin_eta_scan_range_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Normal Scan Range:', thin_eta_scan_range_field)
        thin_eta_small_scan_range_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Small Scan Range:', thin_eta_small_scan_range_field)
        thin_eta_scan_step_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Scan Step:', thin_eta_scan_step_field)
        thin_eta_nudge_field = QSpinBox()
        scan_layout.addRow('Thin Etalon Scan Nudge:', thin_eta_nudge_field)
        return scan_options

    def create_locking_options(self):
        locking_options = QGroupBox('Locking/Stabilization')
        locking_layout = QFormLayout()
        locking_options.setLayout(locking_layout)
        locking_timeout_field = QDoubleSpinBox()
        locking_timeout_field.setMinimum(0)
        locking_layout.addRow('Locking timeout: ', locking_timeout_field)
        pz_eta_correction_pos_field = QDoubleSpinBox()
        pz_eta_correction_pos_field.setMinimum(Matisse.PIEZO_ETALON_LOWER_LIMIT)
        pz_eta_correction_pos_field.setMaximum(Matisse.PIEZO_ETALON_UPPER_LIMIT)
        locking_layout.addRow('Piezo Etalon Correction Pos: ', pz_eta_correction_pos_field)
        slow_pz_correction_pos_field = QDoubleSpinBox()
        slow_pz_correction_pos_field.setMinimum(Matisse.SLOW_PIEZO_LOWER_LIMIT)
        slow_pz_correction_pos_field.setMaximum(Matisse.SLOW_PIEZO_UPPER_LIMIT)
        locking_layout.addRow('Slow Piezo Correction Pos: ', slow_pz_correction_pos_field)
        refcell_correction_pos_field = QDoubleSpinBox()
        refcell_correction_pos_field.setMinimum(Matisse.REFERENCE_CELL_LOWER_LIMIT)
        refcell_correction_pos_field.setMaximum(Matisse.REFERENCE_CELL_UPPER_LIMIT)
        locking_layout.addRow('RefCell Correction Pos: ', refcell_correction_pos_field)
        return locking_options

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Save).clicked.connect(self.save_configuration)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.cancel)
        self.layout.addWidget(button_box)

    def set_configuration(self):
        # TODO: Extract values from form
        self.config['scanning'] = {
            'birefringent_filter': {
                'scan_range': 0,
                'scan_range_small': 0,
                'step': 0
            },
            'thin_etalon': {
                'scan_range': 0,
                'scan_range_small': 0,
                'step': 0,
                'nudge': 0
            }
        }
        self.config['locking'] = {
            'timeout': 0
        }

    @pyqtSlot(bool)
    def save_configuration(self, checked):
        print('Saving configuration.')
        self.set_configuration()
        with open('config.json', 'w') as config_file:
            config_file.write(json.dumps(self.config, indent=4))
        self.close()

    @pyqtSlot(bool)
    def cancel(self, checked):
        self.close()


if __name__ == '__main__':
    app = QApplication([])
    d = ConfigurationDialog()
    d.exec()
    app.exit(0)

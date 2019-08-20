from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import *

import matisse_controller.config as cfg
import matisse_controller.shamrock_ple.ple as ple


class PLEScanDialog(QDialog):
    """A dialog for setting options needed to perform a PLE scan."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('PLE Scan Parameters')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setup_form()
        self.setup_slots()
        self.add_buttons()
        self.setMinimumWidth(400)
        self.scan_location = None

    def setup_form(self):
        form_layout = QFormLayout()
        self.scan_name_field = QLineEdit()
        form_layout.addRow('Scan name: ', self.scan_name_field)

        scan_location_layout = QHBoxLayout()
        self.scan_location_button = QPushButton('Select Folder')
        self.scan_location_label = QLabel()
        scan_location_layout.addWidget(self.scan_location_button)
        scan_location_layout.addWidget(self.scan_location_label)
        form_layout.addRow('Scan Location: ', scan_location_layout)

        self.wavelength_start_field = QDoubleSpinBox()
        self.wavelength_start_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.wavelength_start_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.wavelength_start_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.wavelength_start_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        form_layout.addRow('Wavelength start (nm): ', self.wavelength_start_field)
        self.wavelength_end_field = QDoubleSpinBox()
        self.wavelength_end_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.wavelength_end_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.wavelength_end_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.wavelength_end_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        form_layout.addRow('Wavelength end (nm): ', self.wavelength_end_field)
        self.wavelength_step_field = QDoubleSpinBox()
        self.wavelength_step_field.setMinimum(0)
        self.wavelength_step_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.wavelength_step_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        form_layout.addRow('Wavelength step (nm): ', self.wavelength_step_field)
        self.exposure_time_field = QDoubleSpinBox()
        self.exposure_time_field.setMinimum(0)
        self.exposure_time_field.setDecimals(4)
        form_layout.addRow('Exposure time (s): ', self.exposure_time_field)
        self.layout.addLayout(form_layout)

        # We need to make sure the Andor libraries are loaded to access the spectrometer
        ple.PLE.load_andor_libs()

        self.center_wavelength_field = QDoubleSpinBox()
        self.center_wavelength_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.center_wavelength_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.center_wavelength_field.setValue(ple.shamrock.get_center_wavelength())
        form_layout.addRow('Center wavelength (nm): ', self.center_wavelength_field)

        self.grating_grooves_field = QComboBox()
        for groove_num in ple.shamrock.gratings.keys():
            self.grating_grooves_field.addItem(f"{groove_num}", ple.shamrock.gratings[groove_num])
        self.grating_grooves_field.setCurrentText(str(ple.shamrock.get_grating_grooves()))
        form_layout.addRow('Grating grooves: ', self.grating_grooves_field)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

        self.plot_analysis_field = QCheckBox()
        form_layout.addRow('Plot analysis in real time? ', self.plot_analysis_field)
        self.integration_start_field = QDoubleSpinBox()
        self.integration_start_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.integration_start_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.integration_start_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_start_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_start_field.setEnabled(False)
        form_layout.addRow('Integration start (nm): ', self.integration_start_field)
        self.integration_end_field = QDoubleSpinBox()
        self.integration_end_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.integration_end_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.integration_end_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_end_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_end_field.setEnabled(False)
        form_layout.addRow('Integration end (nm): ', self.integration_end_field)

    def setup_slots(self):
        self.scan_location_button.clicked.connect(self.select_scan_location)
        self.plot_analysis_field.stateChanged.connect(self.toggle_integration_fields)

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_form_data(self):
        return {
            # The keys here MUST match parameter names in the PLE class
            'scan_name': self.scan_name_field.text(),
            'scan_location': self.scan_location,
            'initial_wavelength': self.wavelength_start_field.value(),
            'final_wavelength': self.wavelength_end_field.value(),
            'step': self.wavelength_step_field.value(),
            'exposure_time': self.exposure_time_field.value(),
            'center_wavelength': self.center_wavelength_field.value(),
            'grating_grooves': int(self.grating_grooves_field.currentText()),
            'plot_analysis': self.plot_analysis_field.isChecked(),
            'integration_start': self.integration_start_field.value(),
            'integration_end': self.integration_end_field.value()
        }

    @pyqtSlot(bool)
    def select_scan_location(self, checked):
        self.scan_location = QFileDialog.getExistingDirectory(None, 'Select Folder', '', QFileDialog.ShowDirsOnly |
                                                              QFileDialog.DontResolveSymlinks)
        self.scan_location_label.setText(self.scan_location)

    @pyqtSlot(int)
    def toggle_integration_fields(self, state):
        self.integration_start_field.setEnabled(state == Qt.Checked)
        self.integration_end_field.setEnabled(state == Qt.Checked)


def main():
    app = QApplication([])
    d = PLEScanDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

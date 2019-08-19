import os

from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import *

import matisse_controller.config as cfg
import matisse_controller.shamrock_ple.ple as ple


class SingleAcquisitionDialog(QDialog):
    """A dialog for setting options needed to perform a single CCD acquisition."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Single Acquisition Parameters')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setup_form()
        self.setup_slots()
        self.add_buttons()
        self.setMinimumWidth(300)
        self.data_file_path = None

    def setup_form(self):
        form_layout = QFormLayout()
        data_file_selection_layout = QHBoxLayout()
        self.data_file_button = QPushButton('Select File')
        self.data_file_label = QLabel()
        data_file_selection_layout.addWidget(self.data_file_button)
        data_file_selection_layout.addWidget(self.data_file_label)
        form_layout.addRow('Existing Data: ', data_file_selection_layout)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

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

    def setup_slots(self):
        self.data_file_button.clicked.connect(self.select_data_file)

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_form_data(self):
        return {
            # The keys here MUST match parameter names in the PLE class
            'exposure_time': self.exposure_time_field.value(),
            'center_wavelength': self.center_wavelength_field.value(),
            'grating_grooves': int(self.grating_grooves_field.currentText()),
            'data_file': self.data_file_path,
            'cool_down': False
        }

    @pyqtSlot(bool)
    def select_data_file(self, checked):
        self.data_file_path, success = QFileDialog.getOpenFileName(caption='Select Data File',
                                                          filter='Text file (*.txt)')
        self.data_file_label.setText(os.path.basename(self.data_file_path))


def main():
    app = QApplication([])
    d = SingleAcquisitionDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

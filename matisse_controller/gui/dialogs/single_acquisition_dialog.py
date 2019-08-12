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
        self.add_buttons()

    def setup_form(self):
        form_layout = QFormLayout()
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
            'cool_down': False
        }


def main():
    app = QApplication([])
    d = SingleAcquisitionDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

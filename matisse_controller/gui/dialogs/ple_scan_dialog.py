from PyQt5.QtWidgets import *

import matisse_controller.config as cfg


class PLEScanDialog(QDialog):
    """A dialog for setting options needed to perform a PLE scan."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('PLE Scan Parameters')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setup_form()
        self.add_buttons()

    def setup_form(self):
        form_layout = QFormLayout()
        self.scan_name_field = QLineEdit()
        form_layout.addRow('Scan name: ', self.scan_name_field)
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

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_form_data(self):
        return {
            # The keys here MUST match parameter names in the PLE class
            'name': self.scan_name_field.text(),
            'initial_wavelength': self.wavelength_start_field.value(),
            'final_wavelength': self.wavelength_end_field.value(),
            'step': self.wavelength_step_field.value(),
            'exposure_time': self.exposure_time_field.value()
        }


def main():
    app = QApplication([])
    d = PLEScanDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

from PyQt5.QtWidgets import *

import matisse_controller.config as cfg


class PLEAnalysisDialog(QDialog):
    """A dialog for setting options needed to analyze a PLE scan."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('PLE Analysis Options')
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.setup_form()
        self.add_buttons()

    def setup_form(self):
        form_layout = QFormLayout()
        self.scan_name_field = QLineEdit()
        form_layout.addRow('Scan name: ', self.scan_name_field)
        self.integration_start_field = QDoubleSpinBox()
        self.integration_start_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.integration_start_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.integration_start_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_start_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        form_layout.addRow('Integration start (nm): ', self.integration_start_field)
        self.integration_end_field = QDoubleSpinBox()
        self.integration_end_field.setMinimum(cfg.get(cfg.WAVELENGTH_LOWER_LIMIT))
        self.integration_end_field.setMaximum(cfg.get(cfg.WAVELENGTH_UPPER_LIMIT))
        self.integration_end_field.setDecimals(cfg.get(cfg.WAVEMETER_PRECISION))
        self.integration_end_field.setSingleStep(10 ** -cfg.get(cfg.WAVEMETER_PRECISION))
        form_layout.addRow('Integration end (nm): ', self.integration_end_field)
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
            'integration_start': self.integration_start_field.value(),
            'integration_end': self.integration_end_field.value(),
        }


def main():
    app = QApplication([])
    d = PLEAnalysisDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

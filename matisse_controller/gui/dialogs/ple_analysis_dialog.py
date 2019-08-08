import os

from PyQt5.QtCore import pyqtSlot
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
        self.setup_slots()
        self.add_buttons()
        self.setMinimumWidth(300)
        self.data_file_path = None
        self.background_file_path = None

    def setup_form(self):
        form_layout = QFormLayout()

        data_file_selection_layout = QHBoxLayout()
        self.data_file_button = QPushButton('Select File')
        self.data_file_label = QLabel()
        data_file_selection_layout.addWidget(self.data_file_button)
        data_file_selection_layout.addWidget(self.data_file_label)
        form_layout.addRow('PLE Data: ', data_file_selection_layout)

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

        bkgd_file_selection_layout = QHBoxLayout()
        self.bkgd_file_button = QPushButton('Select File')
        self.bkgd_file_label = QLabel()
        bkgd_file_selection_layout.addWidget(self.bkgd_file_button)
        bkgd_file_selection_layout.addWidget(self.bkgd_file_label)
        form_layout.addRow('Subtract Background: ', bkgd_file_selection_layout)

        self.layout.addLayout(form_layout)

    def setup_slots(self):
        self.data_file_button.clicked.connect(self.select_data_file)
        self.bkgd_file_button.clicked.connect(self.select_background_file)

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.button(QDialogButtonBox.Ok).clicked.connect(self.accept)
        button_box.button(QDialogButtonBox.Cancel).clicked.connect(self.reject)
        self.layout.addWidget(button_box)

    def get_form_data(self):
        return {
            # The keys here MUST match parameter names in the PLE class
            'data_file_path': self.data_file_path,
            'integration_start': self.integration_start_field.value(),
            'integration_end': self.integration_end_field.value(),
            'background_file_path': self.background_file_path
        }

    @pyqtSlot(bool)
    def select_data_file(self, checked):
        self.data_file_path = QFileDialog.getOpenFileName(caption='Select Data File',
                                                          filter='Pickled Data (*.pickle)')[0]
        self.data_file_label.setText(os.path.basename(self.data_file_path))

    @pyqtSlot(bool)
    def select_background_file(self, checked):
        self.background_file_path = QFileDialog.getOpenFileName(caption='Select Background File')[0]
        self.bkgd_file_label.setText(os.path.basename(self.background_file_path))


def main():
    app = QApplication([])
    d = PLEAnalysisDialog()
    if d.exec() == QDialog.Accepted:
        print(d.get_form_data())
    app.exit()


if __name__ == '__main__':
    main()

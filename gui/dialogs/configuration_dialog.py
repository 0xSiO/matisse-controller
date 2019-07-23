from PyQt5.QtWidgets import *


class ConfigurationDialog(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Configuration')
        self.resize(600, 200)
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        self.add_options()
        self.add_buttons()
        # TODO: Load defaults

    def add_options(self):
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

        form = QWidget()
        form_layout = QHBoxLayout()
        form.setLayout(form_layout)
        form_layout.addWidget(scan_options)
        self.layout.addWidget(form)

    def add_buttons(self):
        button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        self.layout.addWidget(button_box)


if __name__ == '__main__':
    app = QApplication([])
    d = ConfigurationDialog()
    d.exec()
    app.exit(0)

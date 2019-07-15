from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QPushButton


class Gui(QApplication):
    def __init__(self):
        super().__init__([])
        window = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QPushButton('Testing'))
        layout.addWidget(QPushButton('GUI'))
        window.setLayout(layout)
        window.show()
        self.exec_()

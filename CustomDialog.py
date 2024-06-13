import serial
import serial.tools.list_ports
from pyqtgraph.Qt import QtCore, QtWidgets
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt


class CustomDialog(QDialog):
    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent)

        self.setStyleSheet("""QLabel {font-size: 10pt;}""")

        self.setWindowTitle("Enter Arduino Settings")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.port = QLineEdit("COM4")
        self.threshold_number = QLineEdit("20")
        self.limit = QLineEdit("50")

        self.detection_radius = QSlider(Qt.Orientation.Horizontal)
        self.detection_radius.setRange(3, 18)
        self.detection_radius.setSingleStep(1)
        self.detection_radius.setTickInterval(1)
        self.detection_radius.setValue(18)
        self.detection_radius.setTickPosition(QSlider.TicksAbove)
        self.detection_label = QLabel("Enter The Scanning Radius (degrees): 180")
        self.detection_radius.valueChanged.connect(self.update_value)
        self.layout = QGridLayout()

        com_list = []
        port_1 = QLabel()
        # Find available ports to connect to
        ports = serial.tools.list_ports.comports()
        for p in ports:
            print(p.device)
            com_list.append(p.device)
        print(len(ports), 'ports found')

        message = QLabel("Enter Port Name")
        port_1.setText("Available Ports:\n" + '\n'.join(com_list))

        self.layout.addWidget(port_1, 0, 0)
        self.layout.addWidget(message, 1, 0)
        self.layout.addWidget(self.port, 2, 0)
        self.layout.addWidget(QLabel("Enter Threshold Detection Range (cm)"), 1, 1)
        self.layout.addWidget(self.threshold_number, 2, 1)
        self.layout.addWidget(QLabel("Enter the Maximum distance to detect (cm)"), 3, 0)
        self.layout.addWidget(self.limit, 4, 0, 1, 2)
        self.layout.addWidget(self.detection_label, 5, 0)
        self.layout.addWidget(self.detection_radius, 6, 0, 1, 2)
        self.layout.addWidget(self.buttonBox, 7, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.setLayout(self.layout)

    def update_value(self):
        self.detection_label.setText("Enter The Scanning Radius (degrees): " + str(self.detection_radius.value() * 10))

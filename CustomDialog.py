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

        #Layout
        self.layout = QGridLayout()
        self.setLayout(self.layout)

        # Port ComboBox and Labels
        com_list = []
        port_1 = QLabel()
        # Find available ports to connect to
        ports = serial.tools.list_ports.comports()

        self.port = QComboBox()
        self.port.setMaxCount(len(ports))

        for index, value in enumerate(sorted(ports)):
            print(index, '\t', value.name, '\t', value.description)
            com_list.append(value.name + '\t' + value.description)
            self.port.addItem(value.name)
        print(len(ports), 'ports found')

        message = QLabel("Select Port Name")
        port_1.setText("Available Ports:\n" + '\n'.join(com_list))

        self.layout.addWidget(port_1, 0, 0)
        self.layout.addWidget(message, 1, 0)
        self.layout.addWidget(self.port, 2, 0)

        # CheckBox for plots
        self.plot1 = QCheckBox("Top Right")
        self.plot2 = QCheckBox("Bottom Right")
        self.plot1.setTristate(False)
        self.plot2.setTristate(False)

        self.layout.addWidget(QLabel("Optional Plots"), 1, 2)
        self.layout.addWidget(self.plot1, 2, 2)
        self.layout.addWidget(self.plot2, 3, 2)
        self.layout.setColumnMinimumWidth(2, 100)

        # Threshold Detection Bounds Labels and LineEdits
        self.threshold_bound1 = QLineEdit("20")
        self.threshold_bound2 = QLineEdit("0")

        self.layout.addWidget(QLabel("Enter Threshold Detection Bound 1 (cm)"), 3, 0)
        self.layout.addWidget(self.threshold_bound1, 4, 0)
        self.layout.addWidget(QLabel("Enter Threshold Detection Bound 2 (cm)"), 3, 1)
        self.layout.addWidget(self.threshold_bound2, 4, 1)

        # Maximum Range Label and LineEdit
        self.limit = QLineEdit("50")

        self.layout.addWidget(QLabel("Enter the Maximum distance to detect (cm)"), 1, 1)
        self.layout.addWidget(self.limit, 2, 1)

        # Detection Radius Slider
        self.detection_radius = QSlider(Qt.Orientation.Horizontal)
        self.detection_radius.setRange(3, 18)
        self.detection_radius.setSingleStep(1)
        self.detection_radius.setTickInterval(1)
        self.detection_radius.setValue(18)
        self.detection_radius.setTickPosition(QSlider.TicksAbove)
        self.detection_label = QLabel("Enter The Scanning Radius (degrees): 180")
        self.detection_radius.valueChanged.connect(self.update_value)

        self.layout.addWidget(self.detection_label, 5, 0)
        self.layout.addWidget(self.detection_radius, 6, 0, 1, 2)

        # Button Box
        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout.addWidget(self.buttonBox, 7, 0, 1, 2, QtCore.Qt.AlignmentFlag.AlignCenter)

    def update_value(self):
        self.detection_label.setText("Enter The Scanning Radius (degrees): " + str(self.detection_radius.value() * 10))

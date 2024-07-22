import serial
import serial.tools.list_ports
from pyqtgraph.Qt import QtCore, QtWidgets, QtGui
from PyQt5.QtWidgets import *
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot
from qt_material import list_themes


class CustomDialog(QDialog):
    new_theme = pyqtSignal(str)

    def __init__(self, parent=None):
        super(CustomDialog, self).__init__(parent)

        self.setStyleSheet("""QLabel { font-size: 10pt; }""")

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
        self.plot1.setChecked(True)
        self.plot2.setChecked(True)

        self.layout.addWidget(QLabel("Optional Plots"), 1, 2)
        self.layout.addWidget(self.plot1, 2, 2)
        self.layout.addWidget(self.plot2, 3, 2)
        self.layout.setColumnMinimumWidth(2, 100)

        # ComboBox for theme colors
        self.color_label = QLabel("Color Theme")
        self.colors = QComboBox()
        self.themes = list_themes()

        for i in range(len(self.themes)):
            x = self.themes[i]
            x = x.replace("_", " ")
            x = x.replace(".xml", "")
            self.colors.addItem(x)
        self.layout.addWidget(self.color_label, 4, 2)
        self.layout.addWidget(self.colors, 5, 2)
        self.colors.currentIndexChanged.connect(self.theme_change)

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

        # Validator
        validator = QtGui.QIntValidator()
        validator.setRange(0, 800)
        self.limit.setValidator(validator)
        self.threshold_bound1.setValidator(validator)
        self.threshold_bound2.setValidator(validator)

        self.limit.inputRejected.connect(self.accept_criteria)
        self.threshold_bound1.inputRejected.connect(self.accept_criteria)
        self.threshold_bound2.inputRejected.connect(self.accept_criteria)

        self.limit.textChanged.connect(self.range_check)
        self.threshold_bound1.textChanged.connect(self.range_check)
        self.threshold_bound2.textChanged.connect(self.range_check)

    def update_value(self):
        self.detection_label.setText("Enter The Scanning Radius (degrees): " + str(self.detection_radius.value() * 10))

    def accept_criteria(self):
        if self.limit.hasAcceptableInput() is False:
            self.limit.setText("")
        if self.threshold_bound1.hasAcceptableInput() is False:
            self.threshold_bound1.setText("")
        if self.threshold_bound2.hasAcceptableInput() is False:
            self.threshold_bound2.setText("")

    def range_check(self):
        try:
            a = int(self.limit.text())
            if a > 800:
                self.limit.setText("")
        except Exception as d:
            print(d)
        try:
            b = int(self.threshold_bound1.text())
            if b > 800:
                self.threshold_bound1.setText("")
        except Exception as e:
            print(e)
        try:
            c = int(self.threshold_bound2.text())
            if c > 800:
                self.threshold_bound2.setText("")
        except Exception as f:
            print(f)

    @pyqtSlot()
    def theme_change(self):
        self.new_theme.emit(self.themes[self.colors.currentIndex()])

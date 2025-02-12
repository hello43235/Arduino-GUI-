##################################################################
# Used in conjunction with Radar_Combined.ino
# GUI Program for small-scale sonar radar composed of an
# Arduino Mega 2560, HC-SR04, and SG-90 servo motor
##################################################################

import sys
import os
import time

import PyQt5
import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import serial
import serial.tools.list_ports

from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot, Qt, QEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QCursor, QPixmap
from pyqtgraph.Qt import QtCore, QtWidgets
from qt_material import apply_stylesheet, list_themes

from SomeObject import SomeObject
from ExportDialog import ExportDialog
from CustomDialog import CustomDialog
from MyBar import MyBar

# noinspection PyArgumentList,PyStatementEffect
stylesheet = list_themes()


# noinspection PyArgumentList
class App(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setWindowTitle("Arduino Project")
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.titleBar = MyBar(self)  # Custom Title Bar
        self.setContentsMargins(0, self.titleBar.height(), 0, 0)
        self.resize(640, self.titleBar.height() + 480)
        self.setMinimumSize(720, 600)  # To avoid being resized too small
        self.setStyleSheet("""QLabel { font-size: 14pt; } """)

        self.arduino = None
        self.port_name = None
        self.file_name = None
        self.det_radius = None
        self.detection_range = None
        self.scan = False
        self.plot1 = None
        self.plot2 = None
        self.index = None
        self.s = 90
        self.color_index = None
        self.current_color = stylesheet[0]
        self.prim_col = os.environ['QTMATERIAL_PRIMARYCOLOR']
        self.shif_col = os.environ['QTMATERIAL_SHIFTEDCOLOR']
        self.sec_light_col = os.environ['QTMATERIAL_SECONDARYTEXTCOLOR']
        self.multiplier = 2
        self.angle_multiplier = 1

        self.titleBar.setStyleSheet('''QPushButton {{ background-color: {}; }}
                                               QPushButton:hover {{ background-color: {}; }}
                                               QLabel {{ color: {}; }}
                '''.format(self.prim_col, os.environ['QTMATERIAL_PRIMARYLIGHTCOLOR'], self.prim_col))
        ################################################################################################################

        ########### Create Gui Elements ###########
        self.mainbox = QtWidgets.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtWidgets.QGridLayout())

        self.canvas = pg.GraphicsLayoutWidget(title="Ultrasonic Sensor")  # Contains all the plots in a gridlayout
        self.mainbox.layout().addWidget(self.canvas, 0, 0, 2, 3)

        # Labels for User Communication
        self.label = QtWidgets.QLabel()  # First Label
        self.label.setMaximumHeight(30)
        self.label2 = QtWidgets.QLabel()  # Second Label
        self.label3 = QtWidgets.QLabel()  # Third Label

        self.box = QGroupBox("User Communication")
        self.box_layout = QVBoxLayout()
        self.box_layout.addWidget(self.label)
        self.box_layout.addWidget(self.label2)
        self.box_layout.addWidget(self.label3)
        self.box.setLayout(self.box_layout)
        self.mainbox.layout().addWidget(self.box, 2, 0, 5, 1)

        # Slider for setting angle
        self.set_angle = QSlider(Qt.Orientation.Horizontal)
        self.set_angle.setToolTip("Sets Static Angle")
        self.set_angle.setRange(0, 180)
        self.set_angle.setSingleStep(1)
        self.set_angle.setTickInterval(1)
        self.set_angle.setValue(180)
        self.set_angle.setTickPosition(QSlider.TicksAbove)
        self.set_angle.setMaximumWidth(930)
        self.set_angle.valueChanged.connect(self.static_angle)
        self.static_timer = QtCore.QTimer()
        self.static_timer.timeout.connect(self.static_scan)
        self.mainbox.layout().addWidget(self.set_angle, 2, 1, 1, 2)
        self.x_static = [0 for _ in range(8)]
        self.y_static = [0 for _ in range(8)]
        self.d_symbol = '\u00b0'

        # Connect to Arduino Button
        self.arduino_button = QPushButton("Connect to Serial Port")
        self.arduino_button.setToolTip("Connects to Specified Serial Port")
        self.arduino_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.arduino_button, 3, 1)
        self.arduino_button.clicked.connect(self.connect_arduino)

        # Start Button
        self.start_button = QPushButton("Start")
        self.start_button.setToolTip("Starts Scanning Function")
        self.start_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.start_button, 3, 2)
        self.start_button.clicked.connect(self.start_timer)

        # Stop Button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setToolTip("Stops All Scanning")
        self.stop_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.stop_button, 4, 2)
        self.stop_button.clicked.connect(self.stop_timer)

        # Settings Button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setToolTip("Opens Settings Window")
        self.settings_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.settings_button, 4, 1)
        self.settings_button.clicked.connect(self.settings)

        # Export to png
        self.export_button = QPushButton("Export")
        self.export_button.setToolTip("Opens Export Window")
        self.export_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.export_button, 5, 1)
        self.export_button.clicked.connect(self.export)

        # Object Detection
        self.obj_det = QPushButton("Object Scanning")
        self.obj_det.setToolTip("Sets Object Scanning Mode")
        self.obj_det.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.obj_det, 5, 2)
        self.obj_det.clicked.connect(self.object_detection)

        # Clear Button
        self.reset = QPushButton("Reset Plots")
        self.reset.setToolTip("Resets All Plots")
        self.reset.setMaximumWidth(465)
        self.reset.setMaximumHeight(95)
        self.mainbox.layout().addWidget(self.reset, 6, 1)
        self.reset.clicked.connect(self.reset_plots)

        # Speed Group Box
        self.speed_box = QGroupBox("Set Scan Speed")
        self.speed_box.setMaximumHeight(95)
        self.speed_box_layout = QHBoxLayout()
        self.speed1 = QRadioButton("1x")
        self.speed1.setToolTip("1x Speed")
        self.speed2 = QRadioButton("2x")
        self.speed2.setToolTip("2x Speed")
        self.speed_box_layout.addWidget(self.speed1)
        self.speed_box_layout.addWidget(self.speed2)
        self.speed_box.setLayout(self.speed_box_layout)
        self.mainbox.layout().addWidget(self.speed_box, 6, 2)
        self.speed1.setChecked(True)

        self.speed1.toggled.connect(self.set_speed)
        self.speed2.toggled.connect(self.set_speed)

        ################################################################################################################

        # Top Left Plot: Ultrasonic Sensor
        self.otherplot = self.canvas.addPlot(0, 0)

        # Bottom Left Plot: Servo
        self.otherplot1 = self.canvas.addPlot(1, 0)

        # Top Right Plot: Radar Image
        self.otherplot2 = self.canvas.addPlot(0, 1)

        # Bottom Right Plot: Radar Image
        self.otherplot3 = self.canvas.addPlot(1, 1)

        # Set Data  #####################

        # Bottom Plot Variables
        self.theta = np.linspace(np.pi / -2, np.pi / 2, 180 * self.multiplier + 1)
        self.radius = [180 for _ in range(180 * self.multiplier + 1)]

        self.ydata1 = [0, self.radius[0] * np.sin(self.theta[0])]  # Radar scanner line
        self.xdata1 = [0, self.radius[0] * np.cos(self.theta[0])]  # initialized at (0, radius)
        self.ydata3 = []
        self.xdata3 = []
        self.ydata5 = []
        self.xdata5 = []
        self.tracking_list_radius = []
        self.tracking_list_azimuth = []
        self.radius1 = []

        self.angle = 0
        self.iter = False
        self.threshold = None
        self.threshold2 = None

        # Top Plot Variables
        self.ydata = [0 for _ in range(200 * self.multiplier)]  # Sets the x range for Top Left Plot
        self.counter = 0

        # For Frame Rate Calculations
        self.fps = 0.
        self.lastupdate = time.time()
        self.now_then = time.time()
        self.now_then2 = time.time()

        # Start  #####################
        self.timer = QtCore.QTimer()  # Timer for regular scanning
        self.timer.timeout.connect(self._update)

        self.detection_timer = QtCore.QTimer()  # Timer for object detection
        self.detection_timer.timeout.connect(self._scanning)

        # Plot Items
        self.plot_items()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.initial_pos = event.pos()
        super().mousePressEvent(event)
        event.accept()

    def mouseMoveEvent(self, event):
        if self.titleBar.state is False:
            if self.initial_pos is not None:
                delta = event.pos() - self.initial_pos
                self.window().move(
                    self.window().x() + delta.x(),
                    self.window().y() + delta.y(),
                )
            super().mouseMoveEvent(event)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.initial_pos = None
        super().mouseReleaseEvent(event)
        event.accept()

    def resizeEvent(self, event):
        self.titleBar.resize(self.width(), self.titleBar.height())

    def set_speed(self):
        if self.speed2.isChecked() is True:
            self.multiplier = 1
            self.angle_multiplier = 2

            self.theta = np.linspace(np.pi / -2, np.pi / 2, 180 * self.multiplier + 1)
            self.radius = [180 for _ in range(180 * self.multiplier + 1)]
            self.radius = [self.s for _ in range(180 * self.multiplier + 1)]
            self.ydata = [0 for _ in range(200 * self.multiplier)]
        elif self.speed1.isChecked() is True:
            self.multiplier = 2
            self.angle_multiplier = 1

            self.theta = np.linspace(np.pi / -2, np.pi / 2, 180 * self.multiplier + 1)
            self.radius = [180 for _ in range(180 * self.multiplier + 1)]
            self.radius = [self.s for _ in range(180 * self.multiplier + 1)]
            self.ydata = [0 for _ in range(200 * self.multiplier)]

    def reset_plots(self):
        """Stops all timers and clears all plots. Functionally a reset button"""
        self.timer.stop()
        self.scan = False
        self.obj_det.setEnabled(True)  # Stop Timers
        self.speed1.setEnabled(True)
        self.speed2.setEnabled(True)
        self.static_timer.stop()

        self.h1.setData()
        self.h2.setData()
        self.h3.setData()
        self.h4.setData()
        self.h5.setData()
        self.h6.setData()  # Clear All Plots
        self.h7.setData()
        self.h8.setData()
        self.h9.setData()
        self.h10.setData()
        self.h_static.setData()
        self.h_static2.setData()
        self.set_limits(self.s)

    def clear_errors(self):
        self.label.setText("")
        self.label2.setText("")
        self.label3.setText("")

    def object_detection(self):
        """Turns on object detection mode, connected to _scanning function"""
        self.clear_errors()
        try:
            self.stop_timer()
            self.angle = 0  # Start scanning from theta = 0
            x = str(self.angle) + "\n"
            self.arduino.write(bytes(x.encode()))  # Move servo to angle
            self.tracking_list_radius = []
            self.tracking_list_azimuth = []
            self.scan = True
            self.speed1.setEnabled(False)
            self.speed2.setEnabled(False)
            self.obj_det.setEnabled(False)  # Disable further user input with button
            self.xdata3 = []
            self.ydata3 = []
            self.h1.setData()  # Clear plots Top Left
            self.h3.setData()  # Bottom Left
            self.h4.setData()  # Bottom Left
            self.h9.setData()  # Top Right Object Detection Line
            self.h10.setData()  # Bottom Right Object Detection Line
        except Exception as a:
            self.label.setText("Error: " + str(a))

    def _scanning(self):
        """Completes 1 sweep from 0 degrees to set radius. While scanning also
            logs data in a .txt file for additional use. Function completes 1 scan
            then user must press start button again to complete another scan.
            used in conjunction with 3d scatter.py"""
        self.obj_det.setEnabled(False)
        self.speed1.setEnabled(False)
        self.speed2.setEnabled(False)
        if self.angle < (self.det_radius * 10) and self.scan is True:  # Scan to the preset radius in settings
            arduinoData = self.arduino.readline().decode('ascii')
            sensorData = float(arduinoData)
            if sensorData > self.s:
                sensorData = self.s
            self.ydata = self.ydata[1:] + [sensorData]
            self.h2.setData(self.ydata, pen=pg.mkPen(self.prim_col))  # Plot distance in Top Left Plot

            self.radius1.append(sensorData)  # For use in determining threshold
            self.ydata2 = (sensorData * np.cos(self.theta[int(self.angle * self.multiplier)]))  # Polar -> Cartesian
            self.xdata2 = (sensorData * np.sin(self.theta[int(self.angle * self.multiplier)]))  # Polar -> Cartesian
            self.ydata2 = float("{:.2f}".format(self.ydata2))
            self.xdata2 = float("{:.2f}".format(self.xdata2))
            self.ydata3.append(self.ydata2)  # List for y-coordinates
            self.xdata3.append(self.xdata2)  # List for x-coordinates
            self.h4.setData(self.xdata3, self.ydata3)  # Update Bottom Left Plot with data points
            self.angle += 0.5 * self.angle_multiplier
            x = str(self.angle) + "\n"
            self.arduino.write(bytes(x.encode()))
            self.tracking_list_radius.append(self.xdata2)  # Array of coordinates for further use
            self.tracking_list_azimuth.append(self.ydata2)
        else:
            self.h9.setData(self.xdata3, self.ydata3)
            self.h10.setData(self.xdata3, self.ydata3)

            with open("datax.txt", 'a+', encoding='utf-8') as f:
                for i in range(len(self.tracking_list_radius)):
                    f.write(str(self.tracking_list_radius[i]) + ",")
                f.write("\n")

            with open("datay.txt", 'a+', encoding='utf-8)') as f:
                for i in range(len(self.tracking_list_azimuth)):
                    f.write(str(self.tracking_list_azimuth[i]) + ",")
                f.write("\n")

            print("Radius: ", self.tracking_list_radius)
            print("Azimuth: ", self.tracking_list_azimuth)
            self.radius1 = []
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData(self.xdata3, self.ydata3)
            self.detection_timer.stop()
            if len(self.tracking_list_radius) == (self.det_radius * 10 * self.multiplier):
                self.object_detection()

    def connect_arduino2(self, s):
        """Connects to an arduino given a port name"""
        try:
            if s == "Success":
                self.arduino = serial.Serial(self.port_name, 9600, bytesize=8)
                self.label.setText("Successfully Connected to " + self.port_name)
                self.arduino_button.setEnabled(True)
            else:
                self.label.setText(s)
        except Exception as a:
            self.label.setText("Error: " + str(a) + " " + str(self.port_name))
            self.arduino_button.setEnabled(True)

    def connect_arduino(self):
        """Creates a thread to connect to the arduino"""
        self.clear_errors()
        self.arduino_button.setEnabled(False)
        # 1 - create Worker and Thread inside the Form
        self.obj = SomeObject()  # no parent!
        self.thread = QThread()  # no parent!

        # 2 - Connect Worker`s Signals to Form method slots to post data.
        self.obj.progress.connect(self.connect_arduino2)

        # 3 - Move the Worker object to the Thread object
        self.obj.moveToThread(self.thread)

        # 4 - Connect Worker Signals to the Thread slots
        self.obj.finished.connect(self.thread.quit)

        # 5 - Connect Thread started signal to Worker operational slot method
        self.thread.started.connect(self.obj.long_running)

        # 6 - Start the thread
        self.thread.start()

    def export(self):
        """Exports current plots to a png file"""
        self.clear_errors()
        self.stop_timer()
        dlg = ExportDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.file_name = dlg.file.text()
            exporter = pg.exporters.ImageExporter(self.canvas.scene())
            exporter.export(self.file_name)
            if self.file_name.lower().endswith('.png'):
                self.label.setText("Successfully saved file as " + self.file_name)
            else:
                self.label.setText("Incorrect File Type")

    def settings(self):
        """Opens a pop-up modeless dialog box it has options for selecting
            the serial COM port, maximum distance, upper and lower bounds
            for object detection, and a scanning radius. Once the user
            inputs their customizations and hits ok it then checks that all
            inputs are valid and accepted. If invalid, reopens dialog box"""
        self.stop_timer()
        dlg = CustomDialog(self)
        dlg.new_theme.connect(self.new_stylesheet)
        if self.index is not None:
            try:
                dlg.port.setCurrentIndex(self.index)
                dlg.colors.setCurrentIndex(self.color_index)
                dlg.limit.setText(str(self.s))
                dlg.detection_radius.setValue(self.det_radius)
                dlg.threshold_bound1.setText(str(self.threshold))
                dlg.threshold_bound2.setText(str(self.threshold2))
                dlg.plot1.setChecked(self.plot1)
                dlg.plot2.setChecked(self.plot2)
            except Exception as a:
                print(a)
        else:
            dlg.colors.setCurrentIndex(3)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.clear_errors()
            try:
                self.port_name = dlg.port.currentText()
                self.index = dlg.port.currentIndex()
                self.color_index = dlg.colors.currentIndex()
                self.threshold = int(dlg.threshold_bound1.text())
                self.threshold2 = int(dlg.threshold_bound2.text())
                self.s = int(dlg.limit.text())
                self.set_limits(self.s)
                self.det_radius = dlg.detection_radius.value()
                if self.s < self.threshold or self.s < self.threshold2:
                    self.clear_errors()
                    self.label3.setText("Error: Threshold Values Out of Range")
                    self.threshold = 20
                    self.threshold2 = 0
                    self.s = 50
                    self.settings()
                else:
                    if self.threshold > self.threshold2:
                        pass
                    elif self.threshold < self.threshold2:
                        upper = self.threshold2
                        lower = self.threshold
                        self.threshold = upper
                        self.threshold2 = lower
                    else:
                        self.clear_errors()
                        self.threshold = 20
                        self.threshold2 = 0
                        self.s = 50
                        self.label2.setText("Error Invalid Threshold Values")
                        self.settings()
                self.plot1 = dlg.plot1.isChecked()
                self.plot2 = dlg.plot2.isChecked()
                print("Plot1 checked: ", self.plot1)
                print("Plot2 checked: ", self.plot2)
                self.checked_plots()
                self.set_limits(self.s)
            except Exception as a:
                print(a)
                self.clear_errors()
                self.s = 50
                self.label2.setText("That's not an integer!")
                self.settings()
        else:
            self.color_index = dlg.colors.currentIndex()

    def new_stylesheet(self, f):
        self.current_color = f
        apply_stylesheet(self.titleBar, theme=f)
        apply_stylesheet(app, theme=f)
        self.prim_col = os.environ['QTMATERIAL_PRIMARYCOLOR']
        self.shif_col = os.environ['QTMATERIAL_SHIFTEDCOLOR']
        self.sec_light_col = os.environ['QTMATERIAL_PRIMARYTEXTCOLOR']
        self.plot_items()
        self.titleBar.setStyleSheet('''QPushButton {{ background-color: {}; }}
                                       QPushButton:hover {{ background-color: {}; }}
                                       QLabel {{ color: {}; }}
        '''.format(self.prim_col, os.environ['QTMATERIAL_PRIMARYLIGHTCOLOR'], self.prim_col))

    def checked_plots(self):
        #Top Plots
        if self.plot1 is False:
            # Remove Plots
            try:
                self.canvas.removeItem(self.otherplot)
            except Exception as a:
                print(a)
            try:
                self.canvas.removeItem(self.otherplot2)
            except Exception as a:
                print(a)

            # Add it back
            self.otherplot = self.canvas.addPlot(0, 0, 1, 2)

        elif self.plot1 is True:
            # Remove Plots
            try:
                self.canvas.removeItem(self.otherplot)
            except Exception as a:
                print(a)
            try:
                self.canvas.removeItem(self.otherplot2)
            except Exception as a:
                print(a)

            # Add it back
            self.otherplot = self.canvas.addPlot(0, 0)
            self.otherplot2 = self.canvas.addPlot(0, 1)

        # Bottom Plots
        if self.plot2 is False:
            # Remove Plots
            try:
                self.canvas.removeItem(self.otherplot3)
            except Exception as a:
                print(a)
            try:
                self.canvas.removeItem(self.otherplot1)
            except Exception as a:
                print(a)

            # Add it back
            self.otherplot1 = self.canvas.addPlot(1, 0, 1, 2)

        elif self.plot2 is True:
            # Remove Plots
            try:
                self.canvas.removeItem(self.otherplot1)
            except Exception as a:
                print(a)
            try:
                self.canvas.removeItem(self.otherplot3)
            except Exception as a:
                print(a)

            # Add it back
            self.otherplot1 = self.canvas.addPlot(1, 0)
            self.otherplot3 = self.canvas.addPlot(1, 1)
        self.plot_items()

    def plot_items(self):

        def top_left():
            # Top Left
            self.h2 = self.otherplot.plot(pen=self.prim_col)

            # Set Grid Lines
            self.otherplot.showGrid(x=True, y=True)
            self.otherplot.setYRange(0, self.s, padding=0)

        def top_right():
            # Top Right Plot
            self.h5 = self.otherplot2.plot([], pen=None, symbolBrush=self.shif_col, symbolSize=2, symbolPen=None)
            self.h6 = self.otherplot2.plot([], pen=None, symbolBrush=self.prim_col, symbolSize=2, symbolPen=None)
            self.h9 = self.otherplot2.plot(pen=self.prim_col)

            self.otherplot2.setYRange(0, self.s, padding=0)
            self.otherplot2.setXRange(-self.s, self.s, padding=0)
            self.otherplot2.addLine(x=0, pen=0.5)
            self.otherplot2.plot([806, -806], [-806, 806], pen=0.5)  # 45 degree line
            self.otherplot2.plot([-806, 806], [-806, 806], pen=0.5)  # 135 degree line

            for r in range(0, 806, 10):
                circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
                circle.setPen(pg.mkPen(0.5))
                self.otherplot2.addItem(circle)

        def bot_left():
            # Bottom Left Plot
            self.h1 = self.otherplot1.plot(pen=self.prim_col)
            self.h3 = self.otherplot1.plot([], pen=None, symbolBrush=self.shif_col, symbolSize=2, symbolPen=None)
            self.h4 = self.otherplot1.plot([], pen=None, symbolBrush=self.prim_col, symbolSize=2, symbolPen=None)
            self.h_static = self.otherplot1.plot([], pen=None, symbolBrush=self.prim_col, symbolSize=5, symbolPen=None)
            self.h_static2 = self.otherplot1.plot([], pen=None, symbolBrush=self.shif_col, symbolSize=2, symbolPen=None)

            self.otherplot1.setYRange(0, self.s, padding=0)
            self.otherplot1.setXRange(-self.s, self.s, padding=0)
            self.otherplot1.addLine(x=0, pen=0.5)
            self.otherplot1.plot([806, -806], [-806, 806], pen=0.5)  # 45 degree line
            self.otherplot1.plot([-806, 806], [-806, 806], pen=0.5)  # 135 degree line

            for r in range(0, 806, 10):  # From 2 to 806 cm at 10 cm intervals
                circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
                circle.setPen(pg.mkPen(0.5))
                self.otherplot1.addItem(circle)

        def bot_right():
            # Bottom Right Plot
            self.h7 = self.otherplot3.plot([], pen=None, symbolBrush=self.shif_col, symbolSize=2, symbolPen=None)
            self.h8 = self.otherplot3.plot([], pen=None, symbolBrush=self.prim_col, symbolSize=2, symbolPen=None)
            self.h10 = self.otherplot3.plot(pen=self.prim_col)

            self.otherplot3.setYRange(0, self.s, padding=0)
            self.otherplot3.setXRange(-self.s, self.s, padding=0)
            self.otherplot3.addLine(x=0, pen=0.5)
            self.otherplot3.plot([806, -806], [-806, 806], pen=0.5)  # 45 degree line
            self.otherplot3.plot([-806, 806], [-806, 806], pen=0.5)  # 135 degree line

            for r in range(0, 806, 10):
                circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
                circle.setPen(pg.mkPen(0.5))
                self.otherplot3.addItem(circle)

        if self.plot1 is None and self.plot2 is None:
            top_left()
            top_right()
            bot_left()
            bot_right()
        if self.plot1 is True:
            top_left()
            top_right()
        else:
            top_left()
        if self.plot2 is True:
            bot_left()
            bot_right()
        else:
            bot_left()

    def set_limits(self, s):
        """Sets limits of each plot according to the maximum range specified
            in the settings dialog box"""
        try:
            self.otherplot.showGrid(x=True, y=True)
            self.otherplot.setYRange(0, s, padding=0)

            self.otherplot1.setYRange(0, s, padding=0)  # Bottom Left Plot
            self.otherplot1.setXRange(-s, s, padding=0)  # Bottom Left Plot

            self.otherplot2.setYRange(0, s, padding=0)  # Top Right Plot
            self.otherplot2.setXRange(-s, s, padding=0)  # Top Right Plot

            self.otherplot3.setYRange(0, s, padding=0)  # Bottom Right Plot
            self.otherplot3.setXRange(-s, s, padding=0)  # Bottom Right Plot

            self.radius = [s for _ in range(180 * self.multiplier + 1)]
            self.detection_range = s
        except Exception as a:
            print(a)
            self.otherplot.showGrid(x=True, y=True)
            self.otherplot.setYRange(0, 90, padding=0)

            self.otherplot1.setYRange(0, 90, padding=0)  # Bottom Left Plot
            self.otherplot1.setXRange(-90, 90, padding=0)  # Bottom Left Plot

            self.otherplot2.setYRange(0, 90, padding=0)  # Top Right Plot
            self.otherplot2.setXRange(-90, 90, padding=0)  # Top Right Plot

            self.otherplot3.setYRange(0, 90, padding=0)  # Bottom Right Plot
            self.otherplot3.setXRange(-90, 90, padding=0)  # Bottom Right Plot

    def start_timer(self):
        """Starts the timer for the scanning features"""
        self.clear_errors()
        self.timer.stop()
        self.obj_det.setEnabled(True)  # Stop Timers
        self.speed1.setEnabled(True)
        self.speed2.setEnabled(True)
        self.static_timer.stop()

        self.h1.setData()
        self.h2.setData()
        self.h3.setData()
        self.h4.setData()
        self.h5.setData()
        self.h6.setData()  # Clear All Plots
        self.h7.setData()
        self.h8.setData()
        self.h9.setData()
        self.h10.setData()
        self.h_static.setData()
        self.h_static2.setData()
        try:
            self.arduino.flushInput()
            if self.scan is False:
                self.timer.start(1)
            else:
                self.detection_timer.start(1)
        except Exception as a:
            self.label.setText("Error: " + str(a))
            self.label2.setText("Error: No Port detected")

    def stop_timer(self):
        """Stops all live plotting timers"""
        try:
            self.angle = 0
            x = str(self.angle) + "\n"
            self.arduino.write(bytes(x.encode()))  # Move servo to angle
        except Exception as a:
            print(a)

        self.timer.stop()
        self.obj_det.setEnabled(True)  # Stop Timers
        self.speed1.setEnabled(True)
        self.speed2.setEnabled(True)
        self.static_timer.stop()
        self.scan = False

        self.ydata1 = [0, self.radius[0] * np.sin(self.theta[0])]  # Radar scanner line
        self.xdata1 = [0, self.radius[0] * np.cos(self.theta[0])]  # initialized at (0, radius)
        self.ydata3 = []
        self.xdata3 = []
        self.ydata5 = []
        self.xdata5 = []

    def static_angle(self):
        """Starts scanning at a stationary angle only"""
        self.label3.setText("")
        self.timer.stop()
        self.detection_timer.stop()
        self.obj_det.setEnabled(True)
        self.speed1.setEnabled(True)
        self.speed2.setEnabled(True)
        self.scan = False
        self.xdata3 = []
        self.ydata3 = []
        self.xdata5 = []
        self.ydata5 = []

        self.h1.setData()
        self.h3.setData()
        self.h4.setData()
        self.h5.setData()
        self.h6.setData()
        self.h7.setData()
        self.h8.setData()
        self.h9.setData()
        self.h10.setData()
        self.angle = self.set_angle.value()
        x = str(self.angle) + "\n"
        try:
            self.arduino.write(bytes(x.encode()))
            self.label.setText("Angle: " + str(self.angle) + self.d_symbol)
        except Exception as a:
            print(a)
            self.label2.setText("Error: Not Connected")

        self.static_timer.start(1)

    def static_scan(self):
        """Scanning function that updates live plots"""
        # Read Data From Arduino
        try:
            arduinoData = self.arduino.readline().decode('ascii')
            sensorData = arduinoData.replace("\r\n", "")
            sensorData = float(sensorData)
        except Exception as a:
            self.label.setText(str(a))
            print("Error With Communications From Arduino")
            print(str(a))
            sensorData = 0

        self.ydata = self.ydata[1:] + [sensorData]

        # Line Plot
        if self.threshold <= sensorData <= self.detection_range or sensorData <= self.threshold2:
            self.h2.setData(self.ydata, pen=pg.mkPen(self.prim_col))
        elif self.threshold2 < sensorData < self.threshold:
            self.h2.setData(self.ydata, pen=pg.mkPen(self.shif_col))
        self.angle = int(self.angle)
        # Bottom Left Plot
        ydata_static = (sensorData * np.cos(self.theta[int(self.angle * self.multiplier)]))  # Polar -> Cartesian
        xdata_static = (sensorData * np.sin(self.theta[int(self.angle * self.multiplier)]))  # Polar -> Cartesian
        ydata_static = float(ydata_static)
        xdata_static = float(xdata_static)
        self.x_static = self.x_static[1:] + [xdata_static]
        self.y_static = self.y_static[1:] + [ydata_static]
        self.h_static.setData(self.x_static[6:7], self.y_static[6:7])
        self.h_static2.setData(self.x_static[0:5], self.y_static[0:5])
        string_data = str(sensorData)
        dx = ("Distance: " + string_data + " cm")
        self.label2.setText(dx)

    def _update(self):
        """Scanning function that updates live plot and iterates servo angle
            Also updates labels to display relevant data to user including:
            Mean FPS, Distance to Object, and Time Taken For 1 Sweep"""
        try:
            arduinoData = self.arduino.readline().decode('ascii')
            sensorData = arduinoData.replace("\r\n", "")
            sensorData = float(sensorData)
        except Exception as a:
            self.label.setText(str(a))
            print("Error With Communications From Arduino")
            print(str(a))
            sensorData = 0

        self.ydata = self.ydata[1:] + [sensorData]

        if self.threshold <= sensorData <= self.detection_range or sensorData <= self.threshold2:
            self.h2.setData(self.ydata, pen=pg.mkPen(self.prim_col))
            self.ydata4 = (sensorData * np.cos(self.theta[int(self.angle * self.multiplier)]))

            self.ydata5.append(self.ydata4)
            self.xdata4 = (sensorData * np.sin(self.theta[int(self.angle * self.multiplier)]))

            self.xdata5.append(self.xdata4)
            self.h4.setData(self.xdata5, self.ydata5)

        elif self.threshold2 < sensorData < self.threshold:
            self.h2.setData(self.ydata, pen=pg.mkPen(self.shif_col))
            self.ydata2 = (sensorData * np.cos(self.theta[int(self.angle * self.multiplier)]))

            self.ydata3.append(self.ydata2)
            self.xdata2 = (sensorData * np.sin(self.theta[int(self.angle * self.multiplier)]))

            self.xdata3.append(self.xdata2)
            self.h3.setData(self.xdata3, self.ydata3)
        if self.angle >= (self.det_radius * 10):
            self.iter = True
            self.h5.setData(self.xdata3, self.ydata3)  # Top Right Plot Red
            self.h6.setData(self.xdata5, self.ydata5)  # Top Right Plot Green
            self.h3.setData()
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData()
            self.xdata5 = []
            self.ydata5 = []
        elif self.angle <= 0:
            self.iter = False
            self.h7.setData(self.xdata3, self.ydata3)  # Bottom Right Plot Red
            self.h8.setData(self.xdata5, self.ydata5)  # Bottom Right Plot Green
            self.h3.setData()
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData()
            self.xdata5 = []
            self.ydata5 = []
        if self.iter is False:
            self.angle += 0.5 * self.angle_multiplier
        else:
            self.angle -= 0.5 * self.angle_multiplier
        x = str(self.angle) + "\n"
        self.arduino.write(bytes(x.encode()))

        self.label3.setText("Angle: " + str(self.angle) + self.d_symbol)

        self.ydata1 = [0, self.radius[int(self.angle * self.multiplier)]
                       * np.cos(self.theta[int(self.angle * self.multiplier)])]
        self.xdata1 = [0, self.radius[int(self.angle * self.multiplier)]
                       * np.sin(self.theta[int(self.angle * self.multiplier)])]

        self.h1.setData(self.xdata1, self.ydata1)

        now = time.time()
        dt = (now - self.lastupdate)

        try:
            fps2 = 1.0 / dt
        except Exception as a:
            print(a)
            fps2 = 1
            print("Too Fast!")
        self.lastupdate = now
        self.fps = self.fps * 0.9 + fps2 * 0.1
        tx = 'Mean Frame Rate:  {fps:.3f} FPS'.format(fps=self.fps)
        self.label.setText(tx)
        string_data = str(sensorData)
        dx = ("Distance: " + string_data + " cm")
        self.label2.setText(dx)


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    apply_stylesheet(app, theme=stylesheet[3])
    thisapp = App()
    thisapp.show()
    sys.exit(app.exec_())

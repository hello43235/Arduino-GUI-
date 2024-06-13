import sys
import time

import numpy as np
import pyqtgraph as pg
import pyqtgraph.exporters
import serial
import serial.tools.list_ports
from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot, Qt
from PyQt5.QtWidgets import *
from pyqtgraph.Qt import QtCore, QtWidgets

from SomeObject import SomeObject
from ExportDialog import ExportDialog
from CustomDialog import CustomDialog


class App(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        super(App, self).__init__(parent)
        self.setWindowTitle("Radar Project")
        self.setWindowState(QtCore.Qt.WindowMaximized)
        self.setStyleSheet("""QPushButton { background-color: qlineargradient(spread: pad, x1:0,y1:0.5,x2:1,y2:1,
                                    stop:0 rgb(1, 108, 52),stop:1 rgb(187, 229, 29));
                                    border-style: outset;
                                    border-color: green;
                                    border-width: 2px;
                                    font: Roboto Mono;
                                    border-radius: 10px;
                                    min-width: 10em;
                                    padding: 6px;
                                    }
                                    QPushButton:hover {
                                    color: white;
                                    background-color: qlineargradient(spread: pad, x1:0,y1:0.5,x2:1,y2:1,
                                    stop:0 rgb(52, 1, 108),stop:1 rgb(29, 187, 229));
                                    border-color: blue;
                                    }
                                    QPushButton:disabled {
                                    color: white;
                                    background-color: qlineargradient(spread: pad, x1:0,y1:0.5,x2:1,y2:1,
                                    stop:0 rgb(108, 52, 1),stop:1 rgb(229, 29, 187));
                                    border-color: red;
                                    }
                                    QPushButton:pressed {
                                    color: white;
                                    background-color: qlineargradient(spread: pad, x1:0,y1:0.5,x2:1,y2:1,
                                    stop:0 rgb(108, 52, 1),stop:1 rgb(229, 29, 187));
                                    border-color: red;
                                    }
                                    QMainWindow {
                                    background-color: grey;
                                    }
                                    QLabel {
                                    font-size: 18pt;
                                    }
                                    """)

        self.arduino = None
        self.port_name = None
        self.file_name = None
        self.det_radius = None
        self.detection_range = None
        self.scan = False
        # Create Gui Elements ###########
        self.mainbox = QtWidgets.QWidget()
        self.setCentralWidget(self.mainbox)
        self.mainbox.setLayout(QtWidgets.QGridLayout())

        self.canvas = pg.GraphicsLayoutWidget(title="Ultrasonic Sensor")
        self.mainbox.layout().addWidget(self.canvas, 0, 0, 2, 3)

        # Labels for User Communication
        self.label = QtWidgets.QLabel()
        self.label.setMinimumWidth(625)
        self.mainbox.layout().addWidget(self.label, 2, 0, 1, 1, QtCore.Qt.AlignmentFlag.AlignLeft)
        self.label2 = QtWidgets.QLabel()
        self.mainbox.layout().addWidget(self.label2, 3, 0)
        self.label3 = QtWidgets.QLabel()
        self.mainbox.layout().addWidget(self.label3, 4, 0)

        # Top Left Plot: Ultrasonic Sensor
        self.otherplot = self.canvas.addPlot(0, 0)
        self.otherplot.setMinimumWidth(625)
        self.h2 = self.otherplot.plot(pen='g')

        # Set Tick Interval
        self.tick = self.otherplot.getAxis('left')
        ticks = np.linspace(0, 180, 10)
        self.tick.setTicks([[(v, str(v)) for v in ticks]])
        self.otherplot.showGrid(x=True, y=True)

        self.otherplot.setYRange(0, 180, padding=0)

        # Bottom Left Plot: Servo
        self.otherplot1 = self.canvas.addPlot(1, 0)
        self.h1 = self.otherplot1.plot(pen='g')
        self.h3 = self.otherplot1.plot([], pen=None, symbolBrush=(255, 0, 0), symbolSize=3, symbolPen=None)
        self.h4 = self.otherplot1.plot([], pen=None, symbolBrush=(0, 255, 0), symbolSize=2, symbolPen=None)

        self.otherplot1.setYRange(0, 90, padding=0)
        self.otherplot1.setXRange(-180, 180, padding=0)
        self.otherplot1.addLine(x=0, pen=0.2)
        self.otherplot1.plot([0, -806], [0, 806], pen=0.2)
        self.otherplot1.plot([0, 806], [0, 806], pen=0.2)

        # Top Right Plot: Radar Image
        self.otherplot2 = self.canvas.addPlot(0, 1)
        self.h5 = self.otherplot2.plot([], pen=None, symbolBrush=(255, 0, 0), symbolSize=3, symbolPen=None)
        self.h6 = self.otherplot2.plot([], pen=None, symbolBrush=(0, 255, 0), symbolSize=2, symbolPen=None)
        self.h9 = self.otherplot2.plot(pen='g')

        self.otherplot2.setYRange(0, 90, padding=0)
        self.otherplot2.setXRange(-180, 180, padding=0)
        self.otherplot2.addLine(x=0, pen=0.2)
        self.otherplot2.plot([0, -806], [0, 806], pen=0.2)
        self.otherplot2.plot([0, 806], [0, 806], pen=0.2)

        # Bottom Right Plot: Radar Image
        self.otherplot3 = self.canvas.addPlot(1, 1)
        self.h7 = self.otherplot3.plot([], pen=None, symbolBrush=(255, 0, 0), symbolSize=3, symbolPen=None)
        self.h8 = self.otherplot3.plot([], pen=None, symbolBrush=(0, 255, 0), symbolSize=2, symbolPen=None)
        self.h10 = self.otherplot3.plot(pen='g')

        self.otherplot3.setYRange(0, 90, padding=0)
        self.otherplot3.setXRange(-180, 180, padding=0)
        self.otherplot3.addLine(x=0, pen=0.2)
        self.otherplot3.plot([0, -806], [0, 806], pen=0.2)
        self.otherplot3.plot([0, 806], [0, 806], pen=0.2)

        # Create Polar Plot Grid Lines
        for r in range(2, 806, 10):
            circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.otherplot1.addItem(circle)
        for r in range(2, 806, 10):
            circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.otherplot2.addItem(circle)
        for r in range(2, 806, 10):
            circle = pg.QtWidgets.QGraphicsEllipseItem(-r, -r, r * 2, r * 2)
            circle.setPen(pg.mkPen(0.2))
            self.otherplot3.addItem(circle)

        # Set Data  #####################

        # Bottom Plot Variables
        self.theta = np.linspace(np.pi / -2, np.pi / 2, 181)
        self.radius = [180 for _ in range(181)]

        self.ydata1 = [0, self.radius[0] * np.sin(self.theta[0])]
        self.xdata1 = [0, self.radius[0] * np.cos(self.theta[0])]
        self.ydata3 = []
        self.xdata3 = []
        self.ydata5 = []
        self.xdata5 = []
        self.tracking_list = []
        self.radius1 = []

        self.angle = 0
        self.iter = False
        self.threshold = 50

        # Top Plot Variables
        self.ydata = [0 for _ in range(250)]
        self.counter = 0

        # For Frame Rate Calculations
        self.fps = 0.
        self.lastupdate = time.time()
        self.now_then = time.time()
        self.now_then2 = time.time()

        # Start  #####################
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self._update)

        self.detection_timer = QtCore.QTimer()
        self.detection_timer.timeout.connect(self._scanning)

        # Connect to Arduino Button
        self.arduino_button = QPushButton("Connect to Arduino")
        self.arduino_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.arduino_button, 2, 1)
        self.arduino_button.clicked.connect(self.connect_arduino)

        # Start Button
        self.start_button = QPushButton("Start")
        self.start_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.start_button, 2, 2)
        self.start_button.clicked.connect(self.start_timer)

        # Stop Button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.stop_button, 3, 2)
        self.stop_button.clicked.connect(self.stop_timer)

        # Settings Button
        self.settings_button = QPushButton("Settings")
        self.settings_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.settings_button, 3, 1)
        self.settings_button.clicked.connect(self.settings)

        # Export to png
        self.export_button = QPushButton("Export")
        self.export_button.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.export_button, 4, 1)
        self.export_button.clicked.connect(self.export)

        # Object Detection
        self.obj_det = QPushButton("Object Detection")
        self.obj_det.setMaximumWidth(465)
        self.mainbox.layout().addWidget(self.obj_det, 4, 2)
        self.obj_det.clicked.connect(self.object_detection)

    def object_detection(self):
        try:
            self.timer.stop()
            self.angle = 0
            x = str(self.angle) + "\n"
            self.arduino.write(bytes(x.encode()))
            self.tracking_list = []
            self.scan = True
            self.obj_det.setEnabled(False)
            self.h1.setData()
            self.h3.setData()
            self.h4.setData()
        except Exception as a:
            self.label.setText("Error: "+ str(a))

    def _scanning(self):

        if self.angle < (self.det_radius * 10):
            arduinoData = self.arduino.readline().decode('ascii')
            sensorData = int(arduinoData)
            self.radius1.append(sensorData)
            self.ydata2 = (sensorData * np.cos(self.theta[self.angle]))
            self.ydata3.append(self.ydata2)
            self.xdata2 = (sensorData * np.sin(self.theta[self.angle]))
            self.xdata3.append(self.xdata2)
            self.h4.setData(self.xdata3, self.ydata3)
            self.angle += 1
            x = str(self.angle) + "\n"
            self.arduino.write(bytes(x.encode()))
            self.tracking_list.append([self.xdata2, self.ydata2])
        else:
            self.h9.setData(self.xdata3, self.ydata3)
            self.h10.setData(self.xdata3, self.ydata3)
            a = (sum(self.radius1)/len(self.radius1))
            self.threshold = round(a)
            print(self.tracking_list)
            self.label2.setText("Threshold: " + str(self.threshold) + " Actual: " + str(a))
            self.radius1 = []
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData(self.xdata3, self.ydata3)
            self.obj_det.setEnabled(True)
            self.detection_timer.stop()
            self.scan = False

    def connect_arduino2(self, s):
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
        # Connect to Arduino
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
        self.timer.stop()
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
        self.timer.stop()
        dlg = CustomDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            self.port_name = dlg.port.text()
            self.threshold = int(dlg.threshold_number.text())
            s = int(dlg.limit.text())
            self.set_limits(s)
            self.det_radius = dlg.detection_radius.value()
            # self.connect_arduino()

    def set_limits(self, s):

        ticks = np.linspace(0, 180, 10)
        self.tick.setTicks([[(v, str(v)) for v in ticks]])
        self.otherplot.showGrid(x=True, y=True)
        self.otherplot.setYRange(0, s, padding=0)

        self.otherplot1.setYRange(0, s, padding=0)  # Bottom Left Plot
        self.otherplot1.setXRange(-s, s, padding=0)  # Bottom Left Plot

        self.otherplot2.setYRange(0, s, padding=0)  # Top Right Plot
        self.otherplot2.setXRange(-s, s, padding=0)  # Top Right Plot

        self.otherplot3.setYRange(0, s, padding=0)  # Bottom Right Plot
        self.otherplot3.setXRange(-s, s, padding=0)  # Bottom Right Plot

        self.radius = [s for _ in range(181)]
        self.detection_range = s

    def start_timer(self):
        try:
            self.arduino.flushInput()
            if self.scan is False:
                self.timer.start(10)
            else:
                self.detection_timer.start(10)
        except:
            self.label.setText("Error: No Port detected")

    def stop_timer(self):
        self.timer.stop()

    def _update(self):
        try:
            arduinoData = self.arduino.readline().decode('ascii')
            sensorData = int(arduinoData)
            if sensorData >= 800:
                sensorData = 0
        except:
            print("Error With Communications From Arduino")
            sensorData = 0

        self.ydata = self.ydata[1:] + [sensorData]
        print(sensorData)

        if self.threshold <= sensorData <= self.detection_range:
            self.h2.setData(self.ydata, pen=pg.mkPen('g'))
            self.ydata4 = (sensorData * np.cos(self.theta[self.angle]))

            self.ydata5.append(self.ydata4)
            self.xdata4 = (sensorData * np.sin(self.theta[self.angle]))

            self.xdata5.append(self.xdata4)
            self.h4.setData(self.xdata5, self.ydata5)
        elif sensorData < self.threshold:
            self.h2.setData(self.ydata, pen=pg.mkPen('r'))
            self.ydata2 = (sensorData * np.cos(self.theta[self.angle]))

            self.ydata3.append(self.ydata2)
            self.xdata2 = (sensorData * np.sin(self.theta[self.angle]))

            self.xdata3.append(self.xdata2)
            self.h3.setData(self.xdata3, self.ydata3)

        if self.angle >= (self.det_radius * 10):
            self.now_then2 = time.time()
            # time.sleep(0.1)
            self.iter = True
            self.h5.setData(self.xdata3, self.ydata3)  # Top Right Plot Red
            self.h6.setData(self.xdata5, self.ydata5)  # Top Right Plot Green
            self.h3.setData()
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData()
            self.xdata5 = []
            self.ydata5 = []
            sweep_time = (time.time() - self.now_then)
            self.label3.setText("Time Taken For 1 Sweep: {0:.2f}".format(sweep_time) + " seconds")
        elif self.angle <= 0:
            self.now_then = time.time()
            # time.sleep(0.1)
            self.iter = False
            self.h7.setData(self.xdata3, self.ydata3)  # Bottom Right Plot Red
            self.h8.setData(self.xdata5, self.ydata5)  # Bottom Right Plot Green
            self.h3.setData()
            self.xdata3 = []
            self.ydata3 = []
            self.h4.setData()
            self.xdata5 = []
            self.ydata5 = []
            sweep_time2 = (time.time() - self.now_then2)
            self.label3.setText("Time Taken For 1 Sweep: {0:.2f}".format(sweep_time2) + " seconds")
        if self.iter is False:
            self.angle += 1
        else:
            self.angle -= 1
        x = str(self.angle) + "\n"
        self.arduino.write(bytes(x.encode()))

        self.label.setText("Angle: " + x)

        self.ydata1 = [0, self.radius[self.angle] * np.cos(self.theta[self.angle])]
        self.xdata1 = [0, self.radius[self.angle] * np.sin(self.theta[self.angle])]

        self.h1.setData(self.xdata1, self.ydata1)

        now = time.time()
        dt = (now - self.lastupdate)

        try:
            fps2 = 1.0 / dt
        except:
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
    thisapp = App()
    thisapp.show()
    sys.exit(app.exec_())
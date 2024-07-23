import PyQt5
import os

from PyQt5.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QStyle, QToolButton
from PyQt5.QtGui import QPalette
from PyQt5.QtCore import Qt, QSize, QPoint
from qt_material import apply_stylesheet


class MyBar(QWidget):
    clickPos = None

    def __init__(self, parent):
        super(MyBar, self).__init__(parent)
        self.setAutoFillBackground(True)
        self.state = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(1, 1, 1, 1)
        layout.addStretch()

        self.title = QLabel("My Own Bar", self, alignment=Qt.AlignCenter)
        # if setPalette() was used above, this is not required

        style = self.style()
        ref_size = self.fontMetrics().height()
        ref_size += style.pixelMetric(style.PM_ButtonMargin) * 2
        self.setMaximumHeight(ref_size + 2)

        btn_size = QSize(ref_size, ref_size)
        for target in ('min', 'normal', 'max', 'close'):
            self.btn = QPushButton(self)
            self.btn.setFocusPolicy(Qt.NoFocus)
            layout.addWidget(self.btn)
            self.btn.setFixedSize(btn_size)

            iconType = getattr(style,
                               'SP_TitleBar{}Button'.format(target.capitalize()))
            self.btn.setIcon(style.standardIcon(iconType))

            signal = getattr(self, target + 'Clicked')
            self.btn.clicked.connect(signal)

            setattr(self, target + 'Button', self.btn)

        self.normalButton.hide()

        self.updateTitle(parent.windowTitle())
        parent.windowTitleChanged.connect(self.updateTitle)

    def updateTitle(self, title=None):
        if title is None:
            title = self.window().windowTitle()
        width = self.title.width()
        width -= self.style().pixelMetric(QStyle.PM_LayoutHorizontalSpacing) * 2
        self.title.setText(self.fontMetrics().elidedText(
            title, Qt.ElideRight, width))

    def closeClicked(self):
        self.window().close()

    def maxClicked(self):
        self.window().showMaximized()
        self.normalButton.setVisible(True)
        self.maxButton.setVisible(False)
        self.state = True

    def normalClicked(self):
        self.window().showNormal()
        self.normalButton.setVisible(False)
        self.maxButton.setVisible(True)
        self.state = False

    def minClicked(self):
        self.window().showMinimized()

    def resizeEvent(self, event):
        self.title.resize(self.minButton.x(), self.height())
        self.updateTitle()

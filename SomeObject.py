import time
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot


class SomeObject(QObject):
    progress = pyqtSignal(str)
    finished = pyqtSignal()

    @pyqtSlot()
    def long_running(self):

        count = 0
        while count < 4:
            if count == 0:
                status = "Connecting ."
                self.progress.emit(status)
                time.sleep(0.5)
            elif count == 1:
                status = "Connecting . ."
                self.progress.emit(status)
                time.sleep(0.5)
            elif count == 2:
                status = "Connecting . . ."
                self.progress.emit(status)
                time.sleep(0.5)
            elif count == 3:
                self.progress.emit("Success")

            count += 1
        self.finished.emit()
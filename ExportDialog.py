from PyQt5.QtWidgets import *


class ExportDialog(QDialog):
    def __init__(self, parent=None):
        super(ExportDialog, self).__init__(parent)

        self.setStyleSheet("""QLabel {font-size: 10pt;}""")

        self.setWindowTitle("Export to PNG")

        QBtn = QDialogButtonBox.Ok | QDialogButtonBox.Cancel

        self.buttonBox = QDialogButtonBox(QBtn)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.layout = QVBoxLayout()
        self.file_name = QLabel("Enter File Name: ")
        self.file = QLineEdit("filename.png")

        self.layout.addWidget(self.file_name)
        self.layout.addWidget(self.file)
        self.layout.addWidget(self.buttonBox)

        self.setLayout(self.layout)

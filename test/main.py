from PyQt6.QtWidgets import QApplication, QWidget, QLabel, QComboBox, QVBoxLayout, QPushButton
from PyQt6.QtCore import Qt
import sys
import os


from libs.stylesheetModefier import StylesheetModifier


class AlarmClock(QWidget):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Alarm Clock")
        self.resize(500, 500)

        self.style_watcher = StylesheetModifier("src/styles.qss", self)


        self.last_mtime = None

        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        self.label = QLabel("00:00:00")
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        # self.label.setFixedHeight(80)
        main_layout.addWidget(self.label)


        # Add this in initUI method:
        self.button = QPushButton("Set Alarm")
        self.button.setObjectName("alarmButton")
        main_layout.addWidget(self.button)




if __name__ == f"__main__":
    app = QApplication(sys.argv)
    win = AlarmClock()
    win.show()
    sys.exit(app.exec())
import sys
import os
from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication, QWidget, QTextEdit, QVBoxLayout


class FileWatcher(QWidget):
    def __init__(self, filepath):
        super().__init__()

        self.filepath = filepath
        self.last_mtime = None

        layout = QVBoxLayout(self)
        self.viewer = QTextEdit()
        self.viewer.setReadOnly(True)
        layout.addWidget(self.viewer)

        # --- QTimer setup ---
        self.timer = QTimer(self)
        self.timer.setInterval(1000)  # check every 1 sec
        self.timer.timeout.connect(self.check_file)
        self.timer.start()

        self.load_file()

    def load_file(self):
        if not os.path.exists(self.filepath):
            self.viewer.setText("File not found")
            return

        with open(self.filepath, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        self.viewer.setText(content)

        # update stored mtime
        self.last_mtime = os.path.getmtime(self.filepath)

    def check_file(self):
        if not os.path.exists(self.filepath):
            return

        current_mtime = os.path.getmtime(self.filepath)
        if self.last_mtime is None or current_mtime != self.last_mtime:
            self.load_file()  # re-read file
            print("File updated — reloaded")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = FileWatcher("test.txt")   # <- change file path
    w.resize(400, 300)
    w.show()
    sys.exit(app.exec())

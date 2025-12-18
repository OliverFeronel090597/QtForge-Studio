# chart_app.py
import sys
import json
import random
from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QTimer, QUrl
from PyQt6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QHBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel

# ---------------------------
# Bridge: JS -> Python calls
# ---------------------------
class Bridge(QObject):
    # signal emitted when JS sends a message
    jsToPy = pyqtSignal(str)

    @pyqtSlot(str)
    def sendToPy(self, msg: str):
        """Called from JS: bridge.sendToPy('...')"""
        print("[JS -> PY] got:", msg)
        self.jsToPy.emit(msg)


# ---------------------------
# Main window with WebEngine
# ---------------------------
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PyQt6 + Chart.js Example")
        self.resize(1000, 700)

        container = QWidget()
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)

        # Top controls: manual update button
        controls = QHBoxLayout()
        btn_update = QPushButton("Push random data (Python → JS)")
        btn_clear = QPushButton("Clear chart (Python → JS)")
        controls.addWidget(btn_update)
        controls.addWidget(btn_clear)
        controls.addStretch()
        layout.addLayout(controls)

        # Web view
        self.view = QWebEngineView()
        layout.addWidget(self.view, 1)

        # WebChannel bridge
        self.channel = QWebChannel()
        self.bridge = Bridge()
        self.channel.registerObject("bridge", self.bridge)
        self.view.page().setWebChannel(self.channel)

        # Connect signals
        btn_update.clicked.connect(self.push_random_data)
        btn_clear.clicked.connect(self.clear_chart)
        self.bridge.jsToPy.connect(self.on_js_message)

        # Load HTML (Chart.js from CDN + qwebchannel)
        self.view.setHtml(self._html(), QUrl("http://local/"))  # base URL helps resolving relative resources if needed

        # Example: live update every 2s
        self.timer = QTimer(self)
        self.timer.setInterval(2000)
        self.timer.timeout.connect(self.push_random_data)
        self.timer.start()

    def on_js_message(self, msg: str):
        # handle messages from JS (e.g., point clicked)
        print("[PY] Received from JS:", msg)

    def push_random_data(self):
        # Compose a small dataset update: append a point (x label, y value)
        label = f"{len(getattr(self, '_labels', [])) + 1}"
        value = random.randint(0, 100)

        # Keep some client-side state for labels count (for demonstration)
        if not hasattr(self, "_labels"):
            self._labels = []
        self._labels.append(label)

        data = {
            "action": "appendPoint",
            "label": label,
            "value": value
        }
        js = f"window.handlePythonMessage({json.dumps(data)});"
        self.view.page().runJavaScript(js)

    def clear_chart(self):
        data = {"action": "clear"}
        self.view.page().runJavaScript(f"window.handlePythonMessage({json.dumps(data)});")
        self._labels = []

    @staticmethod
    def _html() -> str:
        # Chart.js v4 CDN used; qwebchannel.js is loaded from qt resource
        # The page exposes window.handlePythonMessage(data) to accept Python pushes
        return """

        """

# ----------
# Run app
# ----------
def main():
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

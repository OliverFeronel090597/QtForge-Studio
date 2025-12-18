import sys
import random
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

class DynamicTestUI(QWidget):
    """
    Generates widgets dynamically for testing the live renderer.
    Continuously adds widgets with random types, positions, and signals.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Dynamic Test UI")
        self.resize(800, 600)

        # Layout
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # Timer to add widgets slowly
        self.widget_timer = QTimer()
        self.widget_timer.timeout.connect(self.add_random_widget)
        self.widget_timer.start(500)  # add widget every 0.5 seconds

        # Keep track of widgets
        self.widgets = []

    def add_random_widget(self):
        # Randomly choose widget type
        widget_type = random.choice(['button', 'label', 'lineedit', 'checkbox', 'radiobutton', 'combobox', 'textedit'])
        widget = None

        if widget_type == 'button':
            widget = QPushButton(f"Button {len(self.widgets)+1}")
            widget.clicked.connect(lambda _, w=widget: print(f"{w.text()} clicked"))

        elif widget_type == 'label':
            widget = QLabel(f"Label {len(self.widgets)+1}")
            widget.setStyleSheet(f"color: rgb({random.randint(0,255)},{random.randint(0,255)},{random.randint(0,255)});")

        elif widget_type == 'lineedit':
            widget = QLineEdit()
            widget.setPlaceholderText(f"LineEdit {len(self.widgets)+1}")
            widget.textChanged.connect(lambda text, w=widget: print(f"{w.placeholderText()} text: {text}"))

        elif widget_type == 'checkbox':
            widget = QCheckBox(f"CheckBox {len(self.widgets)+1}")
            widget.stateChanged.connect(lambda state, w=widget: print(f"{w.text()} state: {state}"))

        elif widget_type == 'radiobutton':
            widget = QRadioButton(f"Radio {len(self.widgets)+1}")
            widget.toggled.connect(lambda checked, w=widget: print(f"{w.text()} toggled: {checked}"))

        elif widget_type == 'combobox':
            widget = QComboBox()
            items = [f"Item {i}" for i in range(1, 6)]
            widget.addItems(items)
            widget.currentIndexChanged.connect(lambda idx, w=widget: print(f"{w.currentText()} selected"))

        elif widget_type == 'textedit':
            widget = QTextEdit()
            widget.setPlaceholderText(f"TextEdit {len(self.widgets)+1}")
            widget.textChanged.connect(lambda w=widget: print(f"{w.placeholderText()} changed"))

        if widget:
            self.layout.addWidget(widget)
            self.widgets.append(widget)

        # Optional: remove old widgets to avoid overload
        if len(self.widgets) > 50:
            old_widget = self.widgets.pop(0)
            self.layout.removeWidget(old_widget)
            old_widget.deleteLater()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DynamicTestUI()
    win.show()
    sys.exit(app.exec())

from PyQt6.QtWidgets import QWidget
from PyQt6.QtGui import QPainter, QColor, QLinearGradient, QBrush
from PyQt6.QtCore import Qt, QTimer, QPointF

class AquaRippleWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlag(Qt.WindowType.WindowCloseButtonHint, True)
        self.setMinimumSize(600, 600)
        self.ripples = []  # list of dicts: x, y, radius, max_radius, speed

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_ripples)
        self.timer.start(16)  # ~60 FPS

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.ripples.append({
                'x': event.position().x(),
                'y': event.position().y(),
                'radius': 0,
                'max_radius': 150,
                'speed': 4
            })

    def update_ripples(self):
        new_ripples = []
        for r in self.ripples:
            r['radius'] += r['speed']
            if r['radius'] <= r['max_radius']:
                new_ripples.append(r)
        self.ripples = new_ripples
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Water-like gradient background
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(0, 100, 180))   # dark aqua top
        gradient.setColorAt(1, QColor(0, 200, 255))   # lighter aqua bottom
        painter.fillRect(self.rect(), QBrush(gradient))

        # Draw ripples
        for r in self.ripples:
            alpha = max(0, 180 - int((r['radius']/r['max_radius'])*180))  # fade out
            color = QColor(0, 255, 255, alpha)  # aqua color
            painter.setPen(color)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(QPointF(r['x'], r['y']), r['radius'], r['radius'])

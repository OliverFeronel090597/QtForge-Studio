from PyQt6.QtWidgets import QWidget, QApplication
from PyQt6.QtGui import QPainter, QColor, QFont, QBrush, QLinearGradient
from PyQt6.QtCore import Qt, QTimer, QPointF
import sys
import random
import math

class DynamicPaintWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setMinimumSize(800, 600)
        self.setWindowTitle("HD Dynamic Paint")
        self.showMaximized()  # start maximized

        self.shapes = []
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_animation)
        self.timer.start(16)  # ~60 FPS

        # generate random shapes
        for _ in range(100):  # more shapes for density
            self.shapes.append({
                'x': random.uniform(0, self.width()),
                'y': random.uniform(0, self.height()),
                'size': random.uniform(15, 50),
                'color': QColor(0, random.randint(180,255), 255, 180),  # aqua tone with alpha
                'speed': random.uniform(0.5, 3.0),
                'dir': random.uniform(0, 360)
            })

    def update_animation(self):
        self.angle += 1.5  # smooth rotation
        for s in self.shapes:
            rad = math.radians(s['dir'])
            s['x'] += math.cos(rad) * s['speed']
            s['y'] += math.sin(rad) * s['speed']

            # bounce with smooth direction adjustment
            if s['x'] < 0: 
                s['x'] = 0
                s['dir'] = 180 - s['dir']
            elif s['x'] > self.width(): 
                s['x'] = self.width()
                s['dir'] = 180 - s['dir']

            if s['y'] < 0: 
                s['y'] = 0
                s['dir'] = -s['dir']
            elif s['y'] > self.height(): 
                s['y'] = self.height()
                s['dir'] = -s['dir']

        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background gradient (water-like)
        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, QColor(0, 60, 100))
        gradient.setColorAt(1, QColor(0, 120, 180))
        painter.fillRect(self.rect(), QBrush(gradient))

        # Draw shapes
        for s in self.shapes:
            painter.setBrush(s['color'])
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(QPointF(s['x'], s['y']), s['size']/2, s['size']/2)

        # Rotating text in center
        painter.setPen(QColor(255, 255, 255, 200))
        painter.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        painter.save()
        painter.translate(self.width()/2, self.height()/2)
        painter.rotate(self.angle)
        painter.restore()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = DynamicPaintWidget()
    win.show()
    sys.exit(app.exec())

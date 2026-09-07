from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QLinearGradient, QPainter, QPen
from PySide6.QtWidgets import QProgressBar


class RoundedProgressBar(QProgressBar):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setTextVisible(True)
        self.setMinimumHeight(16)
        self.setRange(0, 1000)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        rect = self.rect().adjusted(1, 1, -1, -1)
        radius = rect.height() / 2

        # ----------------------------
        # Background Track
        # ----------------------------
        painter.setPen(QPen(QColor("#262a34"), 1))
        painter.setBrush(QBrush(QColor("#0b0c10")))
        painter.drawRoundedRect(rect, radius, radius)

        # ----------------------------
        # Compute Percent
        # ----------------------------
        if self.maximum() == self.minimum():
            percent = 0.0
        else:
            percent = (self.value() - self.minimum()) / (
                self.maximum() - self.minimum()
            )

        percent = max(0.0, min(1.0, percent))

        fill_width = rect.width() * percent

        # ----------------------------
        # Fill Bar
        # ----------------------------
        if fill_width > 0:

            # Small visual offset so tiny values don’t stick to edge
            min_visual = radius * 0.8
            if 0 < fill_width < min_visual:
                fill_width = min_visual

            fill_rect = QRectF(
                rect.x(),
                rect.y(),
                fill_width,
                rect.height(),
            )

            gradient = QLinearGradient(
                rect.left(),
                rect.top(),
                rect.right(),
                rect.top(),
            )
            gradient.setColorAt(0, QColor("#2a5cff"))
            gradient.setColorAt(1, QColor("#4f7dff"))

            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(gradient))
            painter.drawRoundedRect(fill_rect, radius, radius)

        # ----------------------------
        # Text (always centered)
        # ----------------------------
        painter.setPen(QColor("#ffffff"))
        painter.drawText(rect, Qt.AlignCenter, self.text())

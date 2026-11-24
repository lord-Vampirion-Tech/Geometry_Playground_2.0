from PySide6.QtCore import Qt, QSize, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import QWidget


class Slider2DValue:
    def __init__(self, x_min, x_max, x_value, x_step,
                 y_min, y_max, y_value, y_step):
        self.x_min = float(x_min)
        self.x_max = float(x_max)
        self.x_step = float(x_step)
        self.y_min = float(y_min)
        self.y_max = float(y_max)
        self.y_step = float(y_step)
        self._x = self._quantize(x_value, self.x_min, self.x_max, self.x_step)
        self._y = self._quantize(y_value, self.y_min, self.y_max, self.y_step)

    @staticmethod
    def _quantize(value, minimum, maximum, step):
        value = max(minimum, min(maximum, float(value)))
        index = round((value - minimum) / step)
        return min(maximum, minimum + index * step)

    @property
    def val(self):
        return self._x, self._y

    def set_values(self, x, y):
        self._x = self._quantize(x, self.x_min, self.x_max, self.x_step)
        self._y = self._quantize(y, self.y_min, self.y_max, self.y_step)


class Slider2DCanvas(QWidget):
    def __init__(self, model, on_change, parent=None):
        super().__init__(parent)
        self.model = model
        self._on_change = on_change
        self.setMinimumSize(150, 150)
        self.setMinimumWidth(150)
        self.setMouseTracking(True)

    def sizeHint(self):
        return QSize(220, 220)

    def _plot_rect(self):
        side = min(self.width(), self.height())
        margin = 9
        side = max(1, side - margin * 2)
        left = (self.width() - side) / 2
        top = (self.height() - side) / 2
        return left, top, side, side

    def _to_screen(self, x, y):
        left, top, width, height = self._plot_rect()
        px = left + (x - self.model.x_min) / (self.model.x_max - self.model.x_min) * width
        py = top + (self.model.y_max - y) / (self.model.y_max - self.model.y_min) * height
        return QPointF(px, py)

    def _from_screen(self, px, py):
        left, top, width, height = self._plot_rect()
        px = max(left, min(left + width, px))
        py = max(top, min(top + height, py))
        x = self.model.x_min + (px - left) / width * (self.model.x_max - self.model.x_min)
        y = self.model.y_max - (py - top) / height * (self.model.y_max - self.model.y_min)
        return x, y

    def _set_from_mouse(self, position):
        x, y = self._from_screen(position.x(), position.y())
        previous = self.model.val
        self.model.set_values(x, y)
        if self.model.val != previous:
            self._on_change(self.model)
            self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._set_from_mouse(event.position())
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.MouseButton.LeftButton:
            self._set_from_mouse(event.position())
            event.accept()
            return
        super().mouseMoveEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        left, top, width, height = self._plot_rect()
        right = left + width
        bottom = top + height

        painter.fillRect(self.rect(), QColor("#20232b"))
        painter.fillRect(int(left), int(top), int(width), int(height), QColor("#252a34"))

        grid_pen = QPen(QColor("#3a414d"), 1)
        painter.setPen(grid_pen)
        divisions = 8
        for i in range(divisions + 1):
            x = left + width * i / divisions
            y = top + height * i / divisions
            painter.drawLine(QPointF(x, top), QPointF(x, bottom))
            painter.drawLine(QPointF(left, y), QPointF(right, y))

        if self.model.x_min <= 0 <= self.model.x_max:
            vertical_axis_x = self._to_screen(0, self.model.y_min).x()
            painter.setPen(QPen(QColor("#4caf50"), 2))
            painter.drawLine(
                QPointF(vertical_axis_x, top),
                QPointF(vertical_axis_x, bottom)
            )

        if self.model.y_min <= 0 <= self.model.y_max:
            horizontal_axis_y = self._to_screen(self.model.x_min, 0).y()
            painter.setPen(QPen(QColor("#ef5350"), 2))
            painter.drawLine(
                QPointF(left, horizontal_axis_y),
                QPointF(right, horizontal_axis_y)
            )

        painter.setPen(QPen(QColor("#8d98a8"), 1))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRect(int(left), int(top), int(width), int(height))

        point = self._to_screen(*self.model.val)
        painter.setPen(QPen(QColor("#ffffff"), 2))
        painter.setBrush(QBrush(QColor("#42a5f5")))
        painter.drawEllipse(point, 7, 7)

        painter.end()

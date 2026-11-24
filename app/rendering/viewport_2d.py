import pyqtgraph as pg
from PySide6.QtWidgets import QWidget, QVBoxLayout


class Viewport2D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.graph = pg.PlotWidget()
        self.graph.setBackground("#20232b")
        self.graph.setAspectLocked(True)
        self.graph.showGrid(x=True, y=True, alpha=0.2)
        self.graph.setXRange(-20, 20, padding=0)
        self.graph.setYRange(-20, 20, padding=0)
        self.graph.setLabel("bottom", "X")
        self.graph.setLabel("left", "Y")
        self._pens = {}
        self._batch_depth = 0
        self._pending_updates = {}
        layout.addWidget(self.graph)

    def _pen(self, color):
        pen = self._pens.get(color)
        if pen is None:
            pen = pg.mkPen(color, width=2)
            self._pens[color] = pen
        return pen

    def begin_update(self):
        self._batch_depth += 1

    def end_update(self):
        if self._batch_depth <= 0:
            return

        self._batch_depth -= 1
        if self._batch_depth == 0 and self._pending_updates:
            pending = tuple(self._pending_updates.values())
            self._pending_updates.clear()
            for obj, item in pending:
                self._apply_update(obj, item)

    def add_object(self, obj):
        points = obj.get_vertices()
        xs = [p[0] for p in points] + [points[0][0]]
        ys = [p[1] for p in points] + [points[0][1]]
        return self.graph.plot(xs, ys, pen=self._pen(obj.color))

    def update_object(self, obj, item):
        if self._batch_depth:
            self._pending_updates[id(obj)] = (obj, item)
            return
        self._apply_update(obj, item)

    def _apply_update(self, obj, item):
        points = obj.get_vertices()
        xs = [p[0] for p in points] + [points[0][0]]
        ys = [p[1] for p in points] + [points[0][1]]
        item.setData(xs, ys, pen=self._pen(obj.color))

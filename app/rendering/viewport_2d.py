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
        layout.addWidget(self.graph)

    def add_object(self, obj):
        points = obj.get_vertices()
        xs = [p[0] for p in points] + [points[0][0]]
        ys = [p[1] for p in points] + [points[0][1]]
        item = self.graph.plot(xs, ys, pen=pg.mkPen(obj.color, width=2))
        return item

    def update_object(self, obj, item):
        points = obj.get_vertices()
        xs = [p[0] for p in points] + [points[0][0]]
        ys = [p[1] for p in points] + [points[0][1]]
        item.setData(xs, ys, pen=pg.mkPen(obj.color, width=2))

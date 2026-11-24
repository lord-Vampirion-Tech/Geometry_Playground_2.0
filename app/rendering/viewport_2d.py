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

  def _pen(self, color, width=2):
    key = (color, float(width))
    pen = self._pens.get(key)
    if pen is None:
      pen = pg.mkPen(color, width=width)
      self._pens[key] = pen
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
    if getattr(obj, "geometry_kind", None) == "point":
      return self.graph.plot(
          [obj.x], [obj.y], pen=None, symbol="o",
          symbolSize=obj.size, symbolBrush=obj.color,
          symbolPen=pg.mkPen(obj.color)
      )

    points = obj.get_vertices()
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if getattr(obj, "closed", False) and points:
      xs.append(points[0][0])
      ys.append(points[0][1])
    width = getattr(obj, "line_width", getattr(obj, "width", 2))
    return self.graph.plot(xs, ys, pen=self._pen(obj.color, width))

  def update_object(self, obj, item):
    if self._batch_depth:
      self._pending_updates[id(obj)] = (obj, item)
      return
    self._apply_update(obj, item)

  def _apply_update(self, obj, item):
    if getattr(obj, "geometry_kind", None) == "point":
      item.setData(
          [obj.x], [obj.y], pen=None, symbol="o",
          symbolSize=obj.size, symbolBrush=obj.color,
          symbolPen=pg.mkPen(obj.color)
      )
      return

    points = obj.get_vertices()
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    if getattr(obj, "closed", False) and points:
      xs.append(points[0][0])
      ys.append(points[0][1])
    line_width = getattr(obj, "line_width", getattr(obj, "width", 2))
    item.setData(xs, ys, pen=self._pen(obj.color, line_width))

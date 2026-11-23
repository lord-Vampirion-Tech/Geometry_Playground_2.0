
"""Двумерные геометрические объекты."""

import math
import pyqtgraph as pg


class Square:
  POINT_NAMES = ("A", "B", "C", "D")

  def __init__(
      self,
      x=0,
      y=0,
      width=16,
      height=16,
      color="#42a5f5"
  ):
    self.x = float(x)
    self.y = float(y)
    self.width = float(width)
    self.height = float(height)
    self.color = color
    self.angle = 0.0

    self.pivot = None

    self._items = []
    self._line_items = []
    self._labels = {}
    self._graph = None

    self._reset_local_vertices()

  # --------------------------------------------------
  # Вершины
  # --------------------------------------------------

  def _reset_local_vertices(self):
    hw = self.width / 2
    hh = self.height / 2

    self.local_vertices = {
        "A": [-hw, -hh],
        "B": [hw, -hh],
        "C": [hw, hh],
        "D": [-hw, hh]
    }

  # --------------------------------------------------
  # Позиция
  # --------------------------------------------------

  def setPos(self, x, y):
    self.x = float(x)
    self.y = float(y)

  # --------------------------------------------------
  # Вращение
  # --------------------------------------------------

  def setRot(self, angle, pivot_x=None, pivot_y=None):
    if (pivot_x is None) != (pivot_y is None):
      raise ValueError(
          "Укажите оба параметра pivot_x и pivot_y"
      )

    self.angle = float(angle)

    if pivot_x is None:
      self.pivot = None
    else:
      self.pivot = (
          float(pivot_x),
          float(pivot_y)
      )

  # --------------------------------------------------
  # Цвет и размеры
  # --------------------------------------------------

  def setColor(self, color):
    self.color = color

  def setSize(self, width, height):
    self.width = float(width)
    self.height = float(height)

    self._reset_local_vertices()

  # --------------------------------------------------
  # Вершины
  # --------------------------------------------------

  def movePoint(self, name, x, y):
    name = name.upper()

    if name not in self.local_vertices:
      raise ValueError(
          f"Неизвестная вершина: {name}"
      )

    px, py = self.pivot or (self.x, self.y)
    rad = math.radians(-self.angle)

    dx = float(x) - px
    dy = float(y) - py

    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)

    self.local_vertices[name] = [
        rx + px - self.x,
        ry + py - self.y
    ]

  def getPoint(self, name):
    name = name.upper()

    if name not in self.POINT_NAMES:
      raise ValueError(
          f"Неизвестная вершина: {name}"
      )

    return self.get_vertices()[name]

  def __getitem__(self, name):
    return self.getPoint(name)

  # --------------------------------------------------
  # Геометрия
  # --------------------------------------------------

  def get_vertices(self):
    rad = math.radians(self.angle)

    cos_a = math.cos(rad)
    sin_a = math.sin(rad)

    pivot_x, pivot_y = self.pivot or (self.x, self.y)

    result = {}

    for name, (lx, ly) in self.local_vertices.items():
      wx = self.x + lx
      wy = self.y + ly

      dx = wx - pivot_x
      dy = wy - pivot_y

      rx = dx * cos_a - dy * sin_a
      ry = dx * sin_a + dy * cos_a

      result[name] = (
          rx + pivot_x,
          ry + pivot_y
      )

    return result

  # --------------------------------------------------
  # Отрисовка
  # --------------------------------------------------

  def draw(self, graph):
    if self._graph is graph and self._line_items:
      self.update_draw()
      return

    self._graph = graph
    self._items = []
    self._line_items = []
    self._labels = {}

    triangles = (
        ("A", "B", "C", "A"),
        ("A", "C", "D", "A")
    )

    pen = pg.mkPen(self.color, width=2)

    for _ in triangles:
      item = pg.PlotDataItem(pen=pen)

      graph.addItem(item)

      self._line_items.append(item)
      self._items.append(item)

    for name in self.POINT_NAMES:
      label = pg.TextItem(
          name,
          color="#ffffff",
          anchor=(0.5, 1.5)
      )

      graph.addItem(label)

      self._labels[name] = label
      self._items.append(label)

    self.update_draw()

  def update_draw(self):
    if not self._line_items or self._graph is None:
      return

    vertices = self.get_vertices()

    triangles = (
        ("A", "B", "C", "A"),
        ("A", "C", "D", "A")
    )

    pen = pg.mkPen(self.color, width=2)

    for item, names in zip(
        self._line_items,
        triangles
    ):
      points = [
          vertices[name]
          for name in names
      ]

      xs = [point[0] for point in points]
      ys = [point[1] for point in points]

      item.setData(xs, ys, pen=pen)

    for name, (x, y) in vertices.items():
      self._labels[name].setPos(x, y)


"""Трёхмерные геометрические объекты."""

import math
import numpy as np
import pyvista as pv


class Cube:
  POINT_NAMES = ("A", "B", "C", "D", "E", "F", "G", "H")

  FACES = np.array([
      4, 0, 3, 2, 1,
      4, 4, 5, 6, 7,
      4, 0, 1, 5, 4,
      4, 1, 2, 6, 5,
      4, 2, 3, 7, 6,
      4, 3, 0, 4, 7
  ])

  def __init__(
      self,
      x=0,
      y=0,
      z=0,
      width=16,
      height=16,
      depth=16,
      color="#42a5f5",
      opacity=1.0
  ):
    self.x = float(x)
    self.y = float(y)
    self.z = float(z)

    self.width = float(width)
    self.height = float(height)
    self.depth = float(depth)

    self.color = color
    self.opacity = float(np.clip(opacity, 0.0, 1.0))

    self.rot_x = 0.0
    self.rot_y = 0.0
    self.rot_z = 0.0

    self._plotter = None
    self._mesh = None
    self._actor = None

    self._reset_local_vertices()

  # --------------------------------------------------
  # Вершины
  # --------------------------------------------------

  def _reset_local_vertices(self):
    hw = self.width / 2
    hh = self.height / 2
    hd = self.depth / 2

    self.local_vertices = {
        "A": [-hw, -hh, -hd],
        "B": [hw, -hh, -hd],
        "C": [hw, hh, -hd],
        "D": [-hw, hh, -hd],

        "E": [-hw, -hh, hd],
        "F": [hw, -hh, hd],
        "G": [hw, hh, hd],
        "H": [-hw, hh, hd]
    }

  # --------------------------------------------------
  # Матрица вращения
  # --------------------------------------------------

  def _rotation_matrix(self):
    rx, ry, rz = map(
        math.radians,
        (self.rot_x, self.rot_y, self.rot_z)
    )

    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    Rx = np.array([
        [1, 0, 0],
        [0, cx, -sx],
        [0, sx, cx]
    ])

    Ry = np.array([
        [cy, 0, sy],
        [0, 1, 0],
        [-sy, 0, cy]
    ])

    Rz = np.array([
        [cz, -sz, 0],
        [sz, cz, 0],
        [0, 0, 1]
    ])

    return Rz @ Ry @ Rx

  # --------------------------------------------------
  # Позиция
  # --------------------------------------------------

  def setPos(self, x, y, z):
    self.x = float(x)
    self.y = float(y)
    self.z = float(z)

  # --------------------------------------------------
  # Вращение
  # --------------------------------------------------

  def setRot(self, x, y, z):
    self.rot_x = float(x)
    self.rot_y = float(y)
    self.rot_z = float(z)

  # --------------------------------------------------
  # Размеры
  # --------------------------------------------------

  def setSize(self, width, height=None, depth=None):
    self.width = float(width)

    self.height = float(
        width if height is None else height
    )

    self.depth = float(
        width if depth is None else depth
    )

    self._reset_local_vertices()

  # --------------------------------------------------
  # Цвет
  # --------------------------------------------------

  def setColor(self, color):
    self.color = color

    if self._actor is not None:
      self._actor.prop.color = color

  def setOpacity(self, opacity):
    self.opacity = float(np.clip(opacity, 0.0, 1.0))

    if self._actor is not None:
      self._actor.prop.opacity = self.opacity

  # --------------------------------------------------
  # Геометрия
  # --------------------------------------------------

  def get_vertices(self):
    rotation = self._rotation_matrix()

    position = np.array([
        self.x,
        self.y,
        self.z
    ])

    result = {}

    for name, local in self.local_vertices.items():
      local_point = np.array(local)

      world_point = (
          rotation @ local_point + position
      )

      result[name] = tuple(
          world_point.tolist()
      )

    return result

  def getPoint(self, name):
    name = name.upper()

    if name not in self.POINT_NAMES:
      raise ValueError(
          f"Неизвестная вершина: {name}"
      )

    return self.get_vertices()[name]

  def __getitem__(self, name):
    return self.getPoint(name)

  def movePoint(self, name, x, y, z):
    name = name.upper()

    if name not in self.POINT_NAMES:
      raise ValueError(
          f"Неизвестная вершина: {name}"
      )

    world = np.array([x, y, z], dtype=float)

    position = np.array([
        self.x,
        self.y,
        self.z
    ])

    local = (
        self._rotation_matrix().T
        @ (world - position)
    )

    self.local_vertices[name] = local.tolist()

  # --------------------------------------------------
  # Отрисовка
  # --------------------------------------------------

  def draw(self, plotter):
    self._plotter = plotter
    

    vertices = self.get_vertices()

    points = np.array([
        vertices[name]
        for name in self.POINT_NAMES
    ])

    self._mesh = pv.PolyData(
        points,
        self.FACES
    )

    self._actor = plotter.add_mesh(
        self._mesh,
        color=self.color,
        opacity=self.opacity,
        show_edges=True,
        edge_color="#ffffff",
        line_width=2,
        show_scalar_bar=False
    )

  def update_draw(self):
    if self._mesh is None:
      return

    vertices = self.get_vertices()

    self._mesh.points = np.array([
        vertices[name]
        for name in self.POINT_NAMES
    ])

    if self._actor is not None:
      self._actor.prop.color = self.color


class BoundingCube(Cube):

  def __init__(
      self,
      minx,
      miny,
      minz,
      maxx,
      maxy,
      maxz,
      color="#42a5f5",
      opacity=1.0
  ):
    minx = float(minx)
    miny = float(miny)
    minz = float(minz)

    maxx = float(maxx)
    maxy = float(maxy)
    maxz = float(maxz)

    if minx > maxx or miny > maxy or minz > maxz:
      raise ValueError(
          "Минимальные координаты не могут быть больше максимальных"
      )

    width = maxx - minx
    height = maxy - miny
    depth = maxz - minz

    x = (minx + maxx) / 2
    y = (miny + maxy) / 2
    z = (minz + maxz) / 2

    super().__init__(
        x=x,
        y=y,
        z=z,
        width=width,
        height=height,
        depth=depth,
        color=color,
        opacity=opacity
    )

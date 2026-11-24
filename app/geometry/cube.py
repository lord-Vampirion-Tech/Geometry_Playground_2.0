import math

import numpy as np
import pyvista as pv

from .base import Drawable


class Cube(Drawable):
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
      height=None,
      depth=None,
      color="#42a5f5",
      opacity=1.0,
      draw_callback=None,
      update_callback=None
  ):
    super().__init__(draw_callback, update_callback)

    self.x = float(x)
    self.y = float(y)
    self.z = float(z)

    self.width = float(width)
    self.height = float(width if height is None else height)
    self.depth = float(width if depth is None else depth)

    self.color = color
    self.opacity = float(np.clip(opacity, 0.0, 1.0))

    self.rot_x = 0.0
    self.rot_y = 0.0
    self.rot_z = 0.0

    self._polydata_cache = None
    self._reset_local_vertices()

  def _reset_local_vertices(self):
    self._polydata_cache = None
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

  def _rotation_matrix(self):
    rx, ry, rz = map(
        math.radians,
        (self.rot_x, self.rot_y, self.rot_z)
    )

    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)

    matrix_x = np.array([
        [1, 0, 0],
        [0, cx, -sx],
        [0, sx, cx]
    ])

    matrix_y = np.array([
        [cy, 0, sy],
        [0, 1, 0],
        [-sy, 0, cy]
    ])

    matrix_z = np.array([
        [cz, -sz, 0],
        [sz, cz, 0],
        [0, 0, 1]
    ])

    return matrix_z @ matrix_y @ matrix_x

  def get_vertices(self):
    rotation = self._rotation_matrix()
    position = np.array([self.x, self.y, self.z], dtype=float)

    return {
        name: tuple((rotation @ np.asarray(vertex) + position).tolist())
        for name, vertex in self.local_vertices.items()
    }

  def getPoint(self, name):
    name = name.upper()

    if name not in self.POINT_NAMES:
      raise ValueError(f"Неизвестная вершина: {name}")

    return self.get_vertices()[name]

  def __getitem__(self, name):
    return self.getPoint(name)

  def movePoint(self, name, x, y, z):
    name = name.upper()

    if name not in self.POINT_NAMES:
      raise ValueError(f"Неизвестная вершина: {name}")

    world = np.array([x, y, z], dtype=float)
    position = np.array([self.x, self.y, self.z], dtype=float)

    local = self._rotation_matrix().T @ (world - position)
    self.local_vertices[name] = local.tolist()
    self._polydata_cache = None
    self.update_draw()

  def to_polydata(self):
    if self._polydata_cache is None:
      points = np.array([
          self.get_vertices()[name]
          for name in self.POINT_NAMES
      ], dtype=float)
      self._polydata_cache = pv.PolyData(points, self.FACES)
    return self._polydata_cache

  def setPos(self, x, y, z):
    position = tuple(map(float, (x, y, z)))
    if position == (self.x, self.y, self.z):
      return
    self.x, self.y, self.z = position
    self._polydata_cache = None
    self.update_draw()

  def setRot(self, x=0, y=0, z=0):
    rotation = tuple(map(float, (x, y, z)))
    if rotation == (self.rot_x, self.rot_y, self.rot_z):
      return
    self.rot_x, self.rot_y, self.rot_z = rotation
    self._polydata_cache = None
    self.update_draw()

  def setSize(self, width, height=None, depth=None):
    size = (float(width), float(width if height is None else height),
            float(width if depth is None else depth))
    if size == (self.width, self.height, self.depth):
      return
    self.width, self.height, self.depth = size
    self._reset_local_vertices()
    self.update_draw()

  def setColor(self, color):
    if color == self.color:
      return
    self.color = color
    self.update_draw()

  def setOpacity(self, opacity):
    opacity = float(np.clip(opacity, 0.0, 1.0))
    if opacity == self.opacity:
      return
    self.opacity = opacity
    self.update_draw()


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
      opacity=1.0,
      draw_callback=None,
      update_callback=None
  ):
    bounds = tuple(map(float, (
        minx, miny, minz,
        maxx, maxy, maxz
    )))

    self._validate_bounds(bounds)

    super().__init__(
        x=(bounds[0] + bounds[3]) / 2,
        y=(bounds[1] + bounds[4]) / 2,
        z=(bounds[2] + bounds[5]) / 2,
        width=bounds[3] - bounds[0],
        height=bounds[4] - bounds[1],
        depth=bounds[5] - bounds[2],
        color=color,
        opacity=opacity,
        draw_callback=draw_callback,
        update_callback=update_callback
    )

    (
        self._minx,
        self._miny,
        self._minz,
        self._maxx,
        self._maxy,
        self._maxz
    ) = bounds

  @staticmethod
  def _validate_bounds(bounds):
    minx, miny, minz, maxx, maxy, maxz = bounds

    if minx > maxx or miny > maxy or minz > maxz:
      raise ValueError(
          "Минимальные координаты не могут быть больше максимальных"
      )

  def setBounds(self, minx, miny, minz, maxx, maxy, maxz):
    bounds = tuple(map(float, (
        minx, miny, minz,
        maxx, maxy, maxz
    )))

    if (
        bounds[0] > bounds[3]
        or bounds[1] > bounds[4]
        or bounds[2] > bounds[5]
    ):
      return

    self._validate_bounds(bounds)

    minx, miny, minz, maxx, maxy, maxz = bounds

    self._minx = minx
    self._miny = miny
    self._minz = minz
    self._maxx = maxx
    self._maxy = maxy
    self._maxz = maxz

    self.x = (minx + maxx) / 2
    self.y = (miny + maxy) / 2
    self.z = (minz + maxz) / 2

    self.width = maxx - minx
    self.height = maxy - miny
    self.depth = maxz - minz

    self._reset_local_vertices()
    self.update_draw()

  def _set_bound(self, name, value):
    bounds = [
        self._minx,
        self._miny,
        self._minz,
        self._maxx,
        self._maxy,
        self._maxz
    ]

    indexes = {
        "minx": 0,
        "miny": 1,
        "minz": 2,
        "maxx": 3,
        "maxy": 4,
        "maxz": 5
    }

    bounds[indexes[name]] = float(value)
    self.setBounds(*bounds)

  @property
  def minx(self):
    return self._minx

  @minx.setter
  def minx(self, value):
    self._set_bound("minx", value)

  @property
  def miny(self):
    return self._miny

  @miny.setter
  def miny(self, value):
    self._set_bound("miny", value)

  @property
  def minz(self):
    return self._minz

  @minz.setter
  def minz(self, value):
    self._set_bound("minz", value)

  @property
  def maxx(self):
    return self._maxx

  @maxx.setter
  def maxx(self, value):
    self._set_bound("maxx", value)

  @property
  def maxy(self):
    return self._maxy

  @maxy.setter
  def maxy(self, value):
    self._set_bound("maxy", value)

  @property
  def maxz(self):
    return self._maxz

  @maxz.setter
  def maxz(self, value):
    self._set_bound("maxz", value)

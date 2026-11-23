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

        self._reset_local_vertices()

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
        self.update_draw()

    def to_polydata(self):
        points = np.array([
            self.get_vertices()[name]
            for name in self.POINT_NAMES
        ], dtype=float)

        return pv.PolyData(points, self.FACES)

    def setPos(self, x, y, z):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)
        self.update_draw()

    def setRot(self, x=0, y=0, z=0):
        self.rot_x = float(x)
        self.rot_y = float(y)
        self.rot_z = float(z)
        self.update_draw()

    def setSize(self, width, height=None, depth=None):
        self.width = float(width)
        self.height = float(width if height is None else height)
        self.depth = float(width if depth is None else depth)
        self._reset_local_vertices()
        self.update_draw()

    def setColor(self, color):
        self.color = color
        self.update_draw()

    def setOpacity(self, opacity):
        self.opacity = float(np.clip(opacity, 0.0, 1.0))
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
        minx, miny, minz = map(float, (minx, miny, minz))
        maxx, maxy, maxz = map(float, (maxx, maxy, maxz))

        if minx > maxx or miny > maxy or minz > maxz:
            raise ValueError(
                "Минимальные координаты не могут быть больше максимальных"
            )

        super().__init__(
            x=(minx + maxx) / 2,
            y=(miny + maxy) / 2,
            z=(minz + maxz) / 2,
            width=maxx - minx,
            height=maxy - miny,
            depth=maxz - minz,
            color=color,
            opacity=opacity,
            draw_callback=draw_callback,
            update_callback=update_callback
        )

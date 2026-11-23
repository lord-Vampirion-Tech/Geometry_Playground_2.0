import numpy as np
import pyvista as pv

from .base import Drawable


class Cube(Drawable):
    FACES = np.array([
        [4, 0, 1, 2, 3], [4, 4, 7, 6, 5],
        [4, 0, 4, 5, 1], [4, 1, 5, 6, 2],
        [4, 2, 6, 7, 3], [4, 3, 7, 4, 0]
    ])

    def __init__(self, x=0, y=0, z=0, width=16, height=None, depth=None,
                 color="#42a5f5", opacity=1.0, draw_callback=None,
                 update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.width = float(width)
        self.height = float(width if height is None else height)
        self.depth = float(width if depth is None else depth)
        self.color = color
        self.opacity = float(opacity)
        self.rot_x = self.rot_y = self.rot_z = 0.0

    def get_vertices(self):
        w, h, d = self.width / 2, self.height / 2, self.depth / 2
        points = np.array([
            [-w, -h, -d], [w, -h, -d], [w, h, -d], [-w, h, -d],
            [-w, -h, d], [w, -h, d], [w, h, d], [-w, h, d]
        ], dtype=float)
        rx, ry, rz = np.radians([self.rot_x, self.rot_y, self.rot_z])
        mx = np.array([[1, 0, 0], [0, np.cos(rx), -np.sin(rx)], [0, np.sin(rx), np.cos(rx)]])
        my = np.array([[np.cos(ry), 0, np.sin(ry)], [0, 1, 0], [-np.sin(ry), 0, np.cos(ry)]])
        mz = np.array([[np.cos(rz), -np.sin(rz), 0], [np.sin(rz), np.cos(rz), 0], [0, 0, 1]])
        points = points @ (mz @ my @ mx).T
        points += np.array([self.x, self.y, self.z])
        return points

    def to_polydata(self):
        return pv.PolyData(self.get_vertices(), self.FACES.ravel())

    def setPos(self, x, y, z):
        self.x, self.y, self.z = float(x), float(y), float(z)
        self.update_draw()

    def setRot(self, x=0, y=0, z=0):
        self.rot_x, self.rot_y, self.rot_z = float(x), float(y), float(z)
        self.update_draw()

    def setSize(self, width, height=None, depth=None):
        self.width = float(width)
        self.height = float(width if height is None else height)
        self.depth = float(width if depth is None else depth)
        self.update_draw()

    def setColor(self, color):
        self.color = color
        self.update_draw()

    def setOpacity(self, opacity):
        self.opacity = float(opacity)
        self.update_draw()

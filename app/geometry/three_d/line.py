import numpy as np
import pyvista as pv
from vtkmodules.util.numpy_support import vtk_to_numpy

from ..base import Drawable


class Line(Drawable):
    def __init__(self, x1=0, y1=0, z1=0, x2=16, y2=0, z2=0,
                 color="#42a5f5", width=2, draw_callback=None, update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.points = np.asarray(((x1, y1, z1), (x2, y2, z2)), dtype=np.float64)
        self.color = color
        self.width = float(width)
        self.opacity = 1.0
        self._polydata_cache = None

    def to_polydata(self):
        if self._polydata_cache is None:
            self._polydata_cache = pv.PolyData(
                self.points.copy(), lines=np.asarray((2, 0, 1), dtype=np.int64)
            )
        else:
            vtk_points = self._polydata_cache.GetPoints()
            np.copyto(vtk_to_numpy(vtk_points.GetData()), self.points)
            vtk_points.GetData().Modified()
            vtk_points.Modified()
            self._polydata_cache.Modified()
        return self._polydata_cache

    def setPoints(self, x1, y1, z1, x2, y2, z2):
        points = np.asarray(((x1, y1, z1), (x2, y2, z2)), dtype=np.float64)
        if np.array_equal(points, self.points):
            return
        self.points[:] = points
        self.update_draw()

    def setColor(self, color):
        if color == self.color:
            return
        self.color = color
        self.update_draw()

    def setWidth(self, width):
        width = float(width)
        if width == self.width:
            return
        self.width = width
        self.update_draw()

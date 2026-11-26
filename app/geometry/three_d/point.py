import numpy as np
import pyvista as pv

from ..base import Drawable


class Point(Drawable):
    RADIUS = 1.0
    OUTLINE_SCALE = 1.06

    def __init__(
        self,
        x=0,
        y=0,
        z=0,
        name=None,
        color="#42a5f5",
        opacity=1.0,
        draw_callback=None,
        update_callback=None
    ):
        super().__init__(draw_callback, update_callback)

        self.x, self.y, self.z = map(float, (x, y, z))
        self.name = None if name is None else str(name)
        self.color = color
        self.opacity = float(np.clip(opacity, 0.0, 1.0))
        self._polydata_cache = None
        self._outline_polydata_cache = None

    def to_polydata(self):
        if self._polydata_cache is None:
            self._polydata_cache = pv.Sphere(
                radius=self.RADIUS,
                center=(0.0, 0.0, 0.0),
                direction=(0.0, 1.0, 0.0),
                theta_resolution=20,
                phi_resolution=20
            )
        return self._polydata_cache

    def to_outline_polydata(self):
        if self._outline_polydata_cache is None:
            self._outline_polydata_cache = pv.Sphere(
                radius=self.RADIUS * self.OUTLINE_SCALE,
                center=(0.0, 0.0, 0.0),
                direction=(0.0, 1.0, 0.0),
                theta_resolution=20,
                phi_resolution=20
            )
        return self._outline_polydata_cache

    def setPos(self, x, y, z):
        position = tuple(map(float, (x, y, z)))
        if position == (self.x, self.y, self.z):
            return

        self.x, self.y, self.z = position
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

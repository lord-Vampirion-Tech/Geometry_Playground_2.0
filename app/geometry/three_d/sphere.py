import pyvista as pv

from ..base import Drawable


class Sphere(Drawable):
    RADIUS = 1.0
    OUTLINE_SCALE = 1.06
    SCALE_GEOMETRY = True

    def __init__(self, x=0, y=0, z=0, radius=8, color="#42a5f5", opacity=1.0,
                 theta_resolution=24, phi_resolution=24,
                 draw_callback=None, update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.x, self.y, self.z = map(float, (x, y, z))
        self.radius = float(radius)
        self.color = color
        self.opacity = max(0.0, min(1.0, float(opacity)))
        self.theta_resolution = int(theta_resolution)
        self.phi_resolution = int(phi_resolution)
        self._polydata_cache = None
        self._outline_polydata_cache = None

    def to_polydata(self):
        if self._polydata_cache is None:
            self._polydata_cache = pv.Sphere(
                radius=self.RADIUS,
                center=(0, 0, 0),
                direction=(0, 1, 0),
                theta_resolution=self.theta_resolution,
                phi_resolution=self.phi_resolution
            )
        return self._polydata_cache

    def to_outline_polydata(self):
        if self._outline_polydata_cache is None:
            self._outline_polydata_cache = pv.Sphere(
                radius=self.RADIUS * self.OUTLINE_SCALE,
                center=(0, 0, 0),
                direction=(0, 1, 0),
                theta_resolution=self.theta_resolution,
                phi_resolution=self.phi_resolution
            )
        return self._outline_polydata_cache

    def setPos(self, x, y, z):
        pos = tuple(map(float, (x, y, z)))
        if pos == (self.x, self.y, self.z):
            return
        self.x, self.y, self.z = pos
        self.update_draw()

    def setRadius(self, radius):
        radius = float(radius)
        if radius == self.radius:
            return
        self.radius = radius
        self.update_draw()

    def setColor(self, color):
        if color == self.color:
            return
        self.color = color
        self.update_draw()

    def setOpacity(self, opacity):
        opacity = max(0.0, min(1.0, float(opacity)))
        if opacity == self.opacity:
            return
        self.opacity = opacity
        self.update_draw()

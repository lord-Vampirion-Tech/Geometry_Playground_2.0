import math

from .base import Drawable2D


class Circle(Drawable2D):
    closed = True

    def __init__(self, x=0, y=0, radius=8, color="#42a5f5", line_width=2,
                 segments=64, draw_callback=None, update_callback=None, width=None):
        super().__init__(draw_callback, update_callback)
        if width is not None:
            line_width = width
        self.x, self.y = map(float, (x, y))
        self.radius = float(radius)
        self.color = color
        self.line_width = float(line_width)
        self.segments = max(12, int(segments))

    def get_vertices(self):
        return [(self.x + self.radius * math.cos(2 * math.pi * i / self.segments),
                 self.y + self.radius * math.sin(2 * math.pi * i / self.segments))
                for i in range(self.segments)]

    def setPos(self, x, y):
        pos = tuple(map(float, (x, y)))
        if pos == (self.x, self.y):
            return
        self.x, self.y = pos
        self.update_draw()

    def setRadius(self, radius):
        radius = float(radius)
        if radius == self.radius:
            return
        self.radius = radius
        self.update_draw()

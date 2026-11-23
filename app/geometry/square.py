import math

from .base import Drawable


class Square(Drawable):
    POINT_NAMES = ("A", "B", "C", "D")

    def __init__(self, x=0, y=0, width=16, height=None, color="#42a5f5",
                 angle=0, draw_callback=None, update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.x = float(x)
        self.y = float(y)
        self.width = float(width)
        self.height = float(width if height is None else height)
        self.color = color
        self.angle = float(angle)

    def get_vertices(self):
        hw, hh = self.width / 2, self.height / 2
        points = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        angle = math.radians(self.angle)
        c, s = math.cos(angle), math.sin(angle)
        return [(self.x + px * c - py * s, self.y + px * s + py * c)
                for px, py in points]

    def setPos(self, x, y):
        self.x, self.y = float(x), float(y)
        self.update_draw()

    def setRot(self, angle, pivot_x=None, pivot_y=None):
        self.angle = float(angle)
        self.update_draw()

    def setSize(self, width, height=None):
        self.width = float(width)
        self.height = float(width if height is None else height)
        self.update_draw()

    def setColor(self, color):
        self.color = color
        self.update_draw()

    def getPoint(self, name):
        try:
            return self.get_vertices()[self.POINT_NAMES.index(name)]
        except ValueError:
            raise KeyError(name) from None

    def __getitem__(self, name):
        return self.getPoint(name)

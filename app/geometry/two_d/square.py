import math

from .base import Drawable2D


class Square(Drawable2D):
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
        position = (float(x), float(y))
        if position == (self.x, self.y):
            return
        self.x, self.y = position
        self.update_draw()

    def setRot(self, angle, pivot_x=None, pivot_y=None):
        angle = float(angle)
        if angle == self.angle:
            return
        self.angle = angle
        self.update_draw()

    def setSize(self, width, height=None):
        size = (float(width), float(width if height is None else height))
        if size == (self.width, self.height):
            return
        self.width, self.height = size
        self.update_draw()

    def setColor(self, color):
        if color == self.color:
            return
        self.color = color
        self.update_draw()

    def getPoint(self, name):
        try:
            return self.get_vertices()[self.POINT_NAMES.index(name)]
        except ValueError:
            raise KeyError(name) from None

    def __getitem__(self, name):
        return self.getPoint(name)

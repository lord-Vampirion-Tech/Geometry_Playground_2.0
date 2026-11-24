from .base import Drawable2D


class Point(Drawable2D):
    geometry_kind = "point"

    def __init__(self, x=0, y=0, color="#42a5f5", size=8,
                 draw_callback=None, update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.x, self.y = map(float, (x, y))
        self.color = color
        self.size = float(size)

    def get_vertices(self):
        return [(self.x, self.y)]

    def setPos(self, x, y):
        pos = tuple(map(float, (x, y)))
        if pos == (self.x, self.y):
            return
        self.x, self.y = pos
        self.update_draw()

    def setSize(self, size):
        size = float(size)
        if size == self.size:
            return
        self.size = size
        self.update_draw()

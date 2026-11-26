from .base import Drawable2D


class Line(Drawable2D):
    geometry_kind = "line"

    def __init__(self, x1=0, y1=0, x2=16, y2=0, color="#42a5f5", line_width=0.15,
                 draw_callback=None, update_callback=None, width=None):
        super().__init__(draw_callback, update_callback)
        if width is not None:
            line_width = float(width) * 0.075
        self.x1, self.y1, self.x2, self.y2 = map(float, (x1, y1, x2, y2))
        self.color = color
        self.line_width = float(line_width)

    def get_vertices(self):
        return [(self.x1, self.y1), (self.x2, self.y2)]

    def setPoints(self, x1, y1, x2, y2):
        points = tuple(map(float, (x1, y1, x2, y2)))
        if points == (self.x1, self.y1, self.x2, self.y2):
            return
        self.x1, self.y1, self.x2, self.y2 = points
        self.update_draw()

    def setWidth(self, width):
        self.setLineWidth(float(width) * 0.075)

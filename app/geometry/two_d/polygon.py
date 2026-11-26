from .base import Drawable2D


class Polygon(Drawable2D):
    closed = True

    def __init__(self, points, color="#42a5f5", line_width=0.15,
                 draw_callback=None, update_callback=None, width=None):
        super().__init__(draw_callback, update_callback)
        if width is not None:
            line_width = float(width) * 0.075
        self.points = self._normalize_points(points)
        if len(self.points) < 3:
            raise ValueError("Polygon должен содержать минимум три точки.")
        self.color = color
        self.line_width = float(line_width)

    @staticmethod
    def _normalize_points(points):
        normalized = []
        for point in points:
            point = tuple(point)
            if len(point) != 2:
                raise ValueError("Каждая точка Polygon должна содержать x и y.")
            normalized.append((float(point[0]), float(point[1])))
        return tuple(normalized)

    def get_vertices(self):
        return list(self.points)

    def setPoints(self, points):
        points = self._normalize_points(points)
        if len(points) < 3:
            raise ValueError("Polygon должен содержать минимум три точки.")
        if points == self.points:
            return
        self.points = points
        self.update_draw()

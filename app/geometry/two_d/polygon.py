from .base import Drawable2D


class Polygon(Drawable2D):
    closed = True

    def __init__(self, points, color="#42a5f5", width=2,
                 draw_callback=None, update_callback=None):
        super().__init__(draw_callback, update_callback)
        self.points = self._normalize_points(points)
        if len(self.points) < 3:
            raise ValueError("Polygon должен содержать минимум три точки.")
        self.color = color
        self.width = float(width)

    @staticmethod
    def _normalize_points(points):
        normalized = tuple((float(point[0]), float(point[1])) for point in points)
        if any(len(point) != 2 for point in points):
            raise ValueError("Каждая точка Polygon должна содержать x и y.")
        return normalized

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

import math

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

    def getCenter(self):
        area_twice = 0.0
        cx = 0.0
        cy = 0.0

        for i, (x1, y1) in enumerate(self.points):
            x2, y2 = self.points[(i + 1) % len(self.points)]
            cross = x1 * y2 - x2 * y1
            area_twice += cross
            cx += (x1 + x2) * cross
            cy += (y1 + y2) * cross

        if math.isclose(area_twice, 0.0):
            count = len(self.points)
            return (
                sum(x for x, _ in self.points) / count,
                sum(y for _, y in self.points) / count,
            )

        return cx / (3.0 * area_twice), cy / (3.0 * area_twice)

    def _rotate(self, angle, pivot):
        angle = math.radians(float(angle))
        px, py = self._normalize_points([pivot])[0]
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        points = []
        for x, y in self.points:
            dx = x - px
            dy = y - py
            points.append((
                px + dx * cos_a - dy * sin_a,
                py + dx * sin_a + dy * cos_a,
            ))

        self.setPoints(points)

    def rotate(self, angle):
        self._rotate(angle, self.getCenter())

    def rotateAroundPoint(self, angle, index):
        self._rotate(angle, self.points[index])

    def rotateAroundCoordinates(self, angle, x, y):
        self._rotate(angle, (x, y))

    def setPoint(self, index, point):
        point = self._normalize_points([point])[0]
        points = list(self.points)
        if points[index] == point:
            return
        points[index] = point
        self.points = tuple(points)
        self.update_draw()

    def setPoints(self, points):
        points = self._normalize_points(points)
        if len(points) < 3:
            raise ValueError("Polygon должен содержать минимум три точки.")
        if points == self.points:
            return
        self.points = points
        self.update_draw()

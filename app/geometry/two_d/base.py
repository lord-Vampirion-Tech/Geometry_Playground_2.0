from ..base import Drawable


class Drawable2D(Drawable):
    geometry_kind = "path"
    closed = False

    def get_vertices(self):
        raise NotImplementedError

    def setColor(self, color):
        if color == self.color:
            return
        self.color = color
        self.update_draw()

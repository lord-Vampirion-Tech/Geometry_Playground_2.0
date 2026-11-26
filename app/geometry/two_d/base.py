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

    def setLineWidth(self, line_width):
        if not hasattr(self, "line_width"):
            raise AttributeError("Этот объект не поддерживает толщину контура.")
        line_width = float(line_width)
        if line_width == self.line_width:
            return
        self.line_width = line_width
        self.update_draw()

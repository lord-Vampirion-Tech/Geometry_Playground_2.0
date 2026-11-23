import pyvista as pv
from pyvistaqt import QtInteractor
from PySide6.QtWidgets import QWidget, QVBoxLayout


class Viewport3D(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.plotter = QtInteractor(self)
        layout.addWidget(self.plotter.interactor)
        self.plotter.set_background("#20232b")
        self.plotter.add_axes()
        self.plotter.show_grid(color="#777777")
        self.plotter.view_isometric()

    def add_object(self, obj):
        return self.plotter.add_mesh(
            obj.to_polydata(), color=obj.color, opacity=obj.opacity,
            show_edges=True, line_width=1
        )

    def update_object(self, obj, actor):
        actor.mapper.SetInputData(obj.to_polydata())
        actor.GetProperty().SetColor(*pv.parse_color(obj.color)[:3])
        actor.GetProperty().SetOpacity(obj.opacity)
        self.plotter.render()

    def closeEvent(self, event):
        self.plotter.close()
        super().closeEvent(event)

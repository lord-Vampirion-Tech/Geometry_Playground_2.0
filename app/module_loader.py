from importlib import import_module
import traceback

from PySide6.QtCore import QObject, QRunnable, Signal


class ModuleLoadSignals(QObject):
    finished = Signal(str, object)


class ModuleLoadTask(QRunnable):
    MODULES = {
        "2D": (
            "app.geometry.two_d",
            "app.rendering.viewport_2d",
        ),
        "3D": (
            "app.geometry.three_d",
            "app.rendering.viewport_3d",
        ),
    }

    def __init__(self, mode):
        super().__init__()
        self.mode = mode
        self.signals = ModuleLoadSignals()

    def run(self):
        try:
            for module_name in self.MODULES[self.mode]:
                import_module(module_name)
        except Exception as error:
            self.signals.finished.emit(
                self.mode,
                f"{type(error).__name__}: {error}\n{traceback.format_exc()}"
            )
            return

        self.signals.finished.emit(self.mode, None)

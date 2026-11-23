from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Qt, QTimer, QElapsedTimer
from PySide6.QtGui import QShortcut, QKeySequence

from project_manager import ProjectManager

from .projects import ProjectsMixin
from .interface import InterfaceMixin
from .camera import CameraMixin
from .scene import SceneMixin
from .animation import AnimationMixin
from .help import HelpMixin

class MainWindow(
    ProjectsMixin,
    InterfaceMixin,
    CameraMixin,
    SceneMixin,
    AnimationMixin,
    HelpMixin,
    QMainWindow
):

    def __init__(self, settings=None):
        super().__init__()

        self.settings = settings

        self.project_manager = ProjectManager(
            self.settings.get_storage_folder()
        )

        self.current_project_id = None
        self.current_project_name = "Новый проект"

        self.is_loading_project = False
        self.is_dirty = False

        self.setWindowTitle("Geometry Playground")
        self.resize(1400, 850)
        self._camera_initialized = False

        self.objects = []
        self.namespace = {}
        self.update_function = None

        self.mode = "2D"

        self.Time = 0.0
        self._time_base = 0.0
        self._is_running = False
        self._clock = QElapsedTimer()

        self._camera_drag_mode = None
        self._last_mouse_pos = None
        self.help_dialog = None

        self.frame_timer = QTimer(self)
        self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
        self.frame_timer.setInterval(16)
        self.frame_timer.timeout.connect(self._on_frame)


        self._create_interface()

        self.shortcut_run = QShortcut(
            QKeySequence("Ctrl+Return"),
            self
        )
        self.shortcut_run.activated.connect(self.run_code)

        self.shortcut_save = QShortcut(
            QKeySequence("Ctrl+S"),
            self
        )
        self.shortcut_save.activated.connect(self.save_project)

        self.editor.textChanged.connect(self.on_editor_changed)

        self.refresh_project_list()

        last_project_id = self.settings.get("last_project_id")

        if last_project_id is not None:
            project = self.project_manager.get_project(last_project_id)

            if project is not None:
                self.load_project(project.id)
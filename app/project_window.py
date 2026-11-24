import io
import sys
import traceback

from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

from PySide6.QtCore import Qt, QTimer, QElapsedTimer, QEvent, QObject
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPlainTextEdit,
    QPushButton,
    QLabel,
    QSizePolicy,
    QCheckBox,
    QMessageBox
)

from .settings import apply_theme
from .code_editor import CodeEditor
from .help_dialog import HelpDialog
from .settings_dialog import SettingsDialog
from .project_store import ProjectStore
from .geometry import (
    Square, Cube, BoundingCube, Point2D, Point3D,
    Line2D, Line3D, Polygon, Circle, Sphere
)
from .ui import ParameterAPI
from .rendering import Viewport2D, Viewport3D
from .code_highlighter import PythonHighlighter
from .crash_handler import report_exception, set_crash_context


class UIKeyEventFilter(QObject):
  def __init__(self, window):
    super().__init__(window)
    self.window = window

  def eventFilter(self, watched, event):
    return self.window._handle_ui_key_event(watched, event)


class ProjectWindow(QMainWindow):

  def __init__(self, project, settings):
    super().__init__()

    self.project = project
    self.settings = settings
    self.store = ProjectStore(Path(project["path"]).parent)
    self.code_saved = True

    self.setWindowTitle(
        f"{project['name']} — Geometry Playground 2.0"
    )

    size_key = (
        "project_2d"
        if project["mode"] == "2D"
        else "project_3d"
    )

    size = settings.get(
        "general",
        "window_sizes",
        size_key,
        default=[1100, 750]
    )

    self.resize(int(size[0]), int(size[1]))

    self.execution_context = {"__name__": "__main__"}
    self.geometry_objects = []
    self._ui_key_bindings = {}
    self._ui_pressed_keys = set()
    app = QApplication.instance()
    self._ui_event_filter = UIKeyEventFilter(self)
    if app is not None:
      app.installEventFilter(self._ui_event_filter)

    central = QWidget()
    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(8)

    set_crash_context(
        f"Проект «{project.get('name', '?')}»: создание панели инструментов")
    self._build_toolbar(root_layout)

    set_crash_context(
        f"Проект «{project.get('name', '?')}»: создание редактора и сцены")
    self._build_workspace(root_layout)

    self.save_shortcut = QShortcut(QKeySequence.StandardKey.Save, self)
    self.save_shortcut.activated.connect(self.save_code)

    set_crash_context(
        f"Проект «{project.get('name', '?')}»: установка центрального виджета")
    self.setCentralWidget(central)

    set_crash_context(f"Проект «{project.get('name', '?')}»: применение темы")
    apply_theme(self, settings)
    self.setStyleSheet(self.styleSheet() + """
    QWidget#editorContainer,
    QWidget#sceneContainer,
    QWidget#parametersContainer {
        border: 1px solid #383838;
        border-radius: 5px;
    }

    QLabel#sectionTitle {
        border: none;
        font-size: 13px;
        font-weight: bold;
        padding: 3px 4px;
    }
""")


  def _register_ui_key(self, key, on_press=None, on_release=None):
    sequence = QKeySequence(key)
    if sequence.isEmpty() or sequence.count() != 1:
      raise ValueError(f"Некорректная клавиша кнопки: {key}")
    normalized = sequence.toString(QKeySequence.SequenceFormat.PortableText).upper()
    self._ui_key_bindings.setdefault(normalized, []).append((on_press, on_release))

  def _handle_ui_key_event(self, watched, event):
    if isinstance(watched, QWidget) and watched is not self and not self.isAncestorOf(watched):
      return False

    if event.type() == QEvent.Type.ApplicationDeactivate:
      for sequence in tuple(self._ui_pressed_keys):
        for _, on_release in tuple(self._ui_key_bindings.get(sequence, ())):
          if on_release is not None:
            on_release()
      self._ui_pressed_keys.clear()
      return False

    if event.type() not in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
      return False

    if isinstance(watched, QWidget) and (
        watched is self.editor or self.editor.isAncestorOf(watched)
    ):
      return False

    modifier_masks = {
        int(Qt.Key.Key_Shift): Qt.KeyboardModifier.ShiftModifier.value,
        int(Qt.Key.Key_Control): Qt.KeyboardModifier.ControlModifier.value,
        int(Qt.Key.Key_Alt): Qt.KeyboardModifier.AltModifier.value,
        int(Qt.Key.Key_Meta): Qt.KeyboardModifier.MetaModifier.value,
    }
    modifiers = event.modifiers().value & ~modifier_masks.get(int(event.key()), 0)
    sequence = QKeySequence(
        int(event.key()) | modifiers
    ).toString(QKeySequence.SequenceFormat.PortableText).upper()
    bindings = self._ui_key_bindings.get(sequence)
    if not bindings:
      return False
    if event.isAutoRepeat():
      return True

    if event.type() == QEvent.Type.KeyPress:
      if sequence in self._ui_pressed_keys:
        return True
      self._ui_pressed_keys.add(sequence)
      for on_press, _ in tuple(bindings):
        if on_press is not None:
          on_press()
    else:
      self._ui_pressed_keys.discard(sequence)
      for _, on_release in tuple(bindings):
        if on_release is not None:
          on_release()

    return True

  def _invoke_ui_callback(self, callback, name, phase):
    try:
      callback()
      if self.update_function is not None:
        self._call_update(self.current_time)
    except Exception:
      self._stop_playback()
      self.execution_status.setText(f"Ошибка кнопки: {name}")
      details = traceback.format_exc()
      self.execution_status.setToolTip(details)
      report_exception(
          f"Обработчик {phase} кнопки «{name}» проекта «{self.project.get('name', '?')}»",
          sys.exc_info()
      )

  def _build_toolbar(self, layout):
    toolbar = QHBoxLayout()
    toolbar.setSpacing(8)

    self.save_button = QPushButton("Сохранить")
    self.save_button.setFixedHeight(32)
    self.save_button.clicked.connect(self.save_code)

    self.run_button = QPushButton("Выполнить код")
    self.run_button.setFixedHeight(32)
    self.run_button.clicked.connect(self._on_run_button)

    self.pause_button = QPushButton("Ⅱ Пауза")
    self.pause_button.setFixedHeight(32)
    self.pause_button.setEnabled(False)
    self.pause_button.clicked.connect(self._toggle_pause)

    self.pause_button.setStyleSheet("""
        QPushButton {
            background-color: #a83232;
            color: white;
        }

        QPushButton:disabled {
            background-color: #593333;
            color: #aaaaaa;
        }
    """)

    self.realtime_checkbox = QCheckBox(
        "Выполнять в реальном времени"
    )

    self.realtime_checkbox.toggled.connect(
        self._on_realtime_toggled
    )

    toolbar.addWidget(self.save_button)
    toolbar.addWidget(self.run_button)
    toolbar.addWidget(self.pause_button)
    toolbar.addWidget(self.realtime_checkbox)
    toolbar.addStretch()

    self.editor_settings_button = QPushButton("Настройки")
    self.editor_settings_button.setFixedHeight(32)
    self.editor_settings_button.clicked.connect(self.open_settings)

    self.help_button = QPushButton("Помощь")
    self.help_button.setFixedHeight(32)
    self.help_button.clicked.connect(self.open_help)

    toolbar.addWidget(self.editor_settings_button)
    toolbar.addWidget(self.help_button)

    layout.addLayout(toolbar)

    self.frame_timer = QTimer(self)
    self.frame_timer.setTimerType(Qt.TimerType.PreciseTimer)
    self.frame_timer.setInterval(8)
    self.frame_timer.timeout.connect(self._on_frame)

    self.clock = QElapsedTimer()
    self._fps_clock = QElapsedTimer()
    self._fps_frames = 0

    self.is_running = False
    self.is_paused = False

    self.time_base = 0.0
    self.current_time = 0.0

    self.update_function = None
    self.execution_namespace = {}
    self.parameter_api = None

  def _build_workspace(self, layout):
    self.main_splitter = QSplitter(
        Qt.Orientation.Horizontal
    )

    self.main_splitter.setChildrenCollapsible(False)

    self._build_editor_panel()
    self._build_scene_panel()

    self.main_splitter.addWidget(self.editor_container)
    self.main_splitter.addWidget(self.scene_container)

    self.main_splitter.setStretchFactor(0, 0)
    self.main_splitter.setStretchFactor(1, 1)

    layout.addWidget(self.main_splitter, 1)

    editor_width = self.settings.get(
        "general",
        "layout_sizes",
        "editor_width",
        default=450
    )

    self.main_splitter.setSizes([
        editor_width,
        max(300, self.width() - editor_width)
    ])

  def _build_editor_panel(self):
    self.editor_container = QWidget()
    self.editor_container.setObjectName("editorContainer")

    editor_layout = QVBoxLayout(self.editor_container)
    editor_layout.setContentsMargins(0, 0, 0, 0)
    editor_layout.setSpacing(6)

    header = QHBoxLayout()

    title = QLabel("Код")
    title.setObjectName("sectionTitle")

    self.execution_status = QLabel("Готово")
    self.simulation_stats_label = QLabel("FPS: 0 | Время: 0.00 с")

    header.addWidget(title)
    header.addStretch()
    header.addWidget(self.simulation_stats_label)
    header.addWidget(self.execution_status)
    editor_layout.addLayout(header)

    self.editor = CodeEditor()
    set_crash_context("Создание редактора и подсветчика Python")
    self.highlighter = PythonHighlighter(self.editor.document())
    self._apply_editor_settings()
    self.editor.setPlaceholderText(
        "Введите код здесь..."
    )
    self.editor.setPlainText(self.store.load_code(self.project))
    self.editor.textChanged.connect(self._on_code_changed)

    editor_layout.addWidget(self.editor, 1)

    self._build_parameters_panel(editor_layout)

  def _build_scene_panel(self):
    self.scene_container = QWidget()
    self.scene_container.setObjectName("sceneContainer")

    scene_layout = QVBoxLayout(self.scene_container)
    scene_layout.setContentsMargins(0, 0, 0, 0)

    title = QLabel("Пространство")
    title.setObjectName("sectionTitle")
    scene_layout.addWidget(title)

    if self.project["mode"] == "2D":
      set_crash_context("Создание 2D-области PyQtGraph")
      self.viewport = Viewport2D(self.scene_container)
    else:
      set_crash_context("Создание 3D-области PyVista/VTK")
      self.viewport = Viewport3D(self.scene_container)

    scene_layout.addWidget(self.viewport, 1)

  def _build_parameters_panel(self, layout):
    self.parameters_container = QWidget()
    self.parameters_container.setObjectName("parametersContainer")

    parameters_layout = QVBoxLayout(
        self.parameters_container
    )

    parameters_layout.setContentsMargins(0, 0, 0, 0)
    parameters_layout.setSpacing(4)

    self.parameters_splitter = QSplitter(
        Qt.Orientation.Horizontal
    )

    self.parameters_splitter.setChildrenCollapsible(False)

    self.parameters_panel = QWidget()
    self.parameters_panel.setMinimumWidth(150)

    panel_layout = QVBoxLayout(self.parameters_panel)
    panel_layout.setContentsMargins(8, 6, 8, 6)

    title = QLabel("UI элементы")
    title.setObjectName("sectionTitle")
    panel_layout.addWidget(title)

    self.parameters_content = QVBoxLayout()
    self.parameters_content.setSpacing(6)

    panel_layout.addLayout(self.parameters_content)
    panel_layout.addStretch()

    self.parameters_spacer = QWidget()
    self.parameters_spacer.setSizePolicy(
        QSizePolicy.Policy.Expanding,
        QSizePolicy.Policy.Preferred
    )

    self.parameters_splitter.addWidget(
        self.parameters_panel
    )

    self.parameters_splitter.addWidget(
        self.parameters_spacer
    )

    parameters_layout.addWidget(
        self.parameters_splitter
    )

    layout.addWidget(self.parameters_container)

    self.parameters_container.hide()

    panel_width = self.settings.get(
        "general",
        "layout_sizes",
        "parameters_panel_width",
        default=450
    )

    self.parameters_splitter.setSizes([
        panel_width,
        max(1, 450 - panel_width)
    ])

  def add_parameter_widget(self, widget):
    self.parameters_content.addWidget(widget)
    self.parameters_container.show()

  def clear_parameter_widgets(self):
    self._ui_key_bindings.clear()
    self._ui_pressed_keys.clear()
    while self.parameters_content.count():
      item = self.parameters_content.takeAt(0)

      widget = item.widget()
      if widget is not None:
        widget.deleteLater()

    self.parameters_container.hide()

  def open_settings(self):
    dialog = SettingsDialog(self.settings, self)
    dialog.settings_applied.connect(self._apply_editor_settings)
    dialog.settings_applied.connect(
        lambda: apply_theme(self, self.settings)
    )
    dialog.settings_applied.connect(self._apply_ui_group_settings)
    dialog.exec()

  def open_help(self):
    HelpDialog(self.project["mode"], self).exec()

  def _apply_ui_group_settings(self):
    if self.parameter_api is None:
      return

    self.parameter_api.layouts.set_group_style(
        self.settings.get("general", "ui_groups", "border_width", default=5),
        self.settings.get("general", "ui_groups",
                          "border_color", default="#000000")
    )

  def _apply_editor_settings(self):
    size = self.settings.get("general", "layout_sizes",
                             "editor_font_size", default=16)
    font = self.editor.font()
    font.setPointSize(int(size))
    self.editor.setFont(font)

  def _on_code_changed(self):
    self.code_saved = False
    self.save_button.setText("Сохранить *")

  def save_code(self):
    try:
      self.store.save_code(self.project, self.editor.toPlainText())
      self.code_saved = True
      self.save_button.setText("Сохранено")
      self.execution_status.setText("Код сохранён")
    except Exception as error:
      QMessageBox.critical(
          self,
          "Ошибка сохранения",
          f"Не удалось сохранить код проекта:\\n{error}"
      )

  def _execute_code(self):
    self._stop_playback()
    self.clear_parameter_widgets()
    self._clear_scene()

    source = self.editor.toPlainText()

    self.execution_status.setText("Выполнение...")
    self._set_run_button(False)

    self.current_time = 0.0
    self.time_base = 0.0
    self._set_simulation_stats(0)

    self._ui_key_bindings.clear()
    self._ui_pressed_keys.clear()
    self.parameter_api = ParameterAPI(
        self,
        self.parameters_content,
        create_widgets=self.realtime_checkbox.isChecked(),
        group_border_width=self.settings.get(
            "general", "ui_groups", "border_width", default=5),
        group_border_color=self.settings.get(
            "general", "ui_groups", "border_color", default="#000000")
    )

    namespace = {
        "__name__": "__main__",
        "ui": self.parameter_api,
    }

    if self.project["mode"] == "2D":
      namespace.update({
          "Point": lambda *args, **kwargs: self._create_geometry(Point2D, *args, **kwargs),
          "Line": lambda *args, **kwargs: self._create_geometry(Line2D, *args, **kwargs),
          "Square": lambda *args, **kwargs: self._create_geometry(Square, *args, **kwargs),
          "Polygon": lambda *args, **kwargs: self._create_geometry(Polygon, *args, **kwargs),
          "Circle": lambda *args, **kwargs: self._create_geometry(Circle, *args, **kwargs)
      })
    else:
      namespace.update({
          "Point": lambda *args, **kwargs: self._create_geometry(Point3D, *args, **kwargs),
          "Line": lambda *args, **kwargs: self._create_geometry(Line3D, *args, **kwargs),
          "Cube": lambda *args, **kwargs: self._create_geometry(Cube, *args, **kwargs),
          "BoundingCube": lambda *args, **kwargs: self._create_geometry(BoundingCube, *args, **kwargs),
          "Sphere": lambda *args, **kwargs: self._create_geometry(Sphere, *args, **kwargs)
      })

    batch_render = hasattr(self.viewport, "begin_update")
    if batch_render:
      self.viewport.begin_update()

    try:
      try:
        exec(
            compile(
                source,
                f"<{self.project['name']}>",
                "exec"
            ),
            namespace,
            namespace
        )

        update_function = namespace.get("update")

        if update_function is not None and not callable(update_function):
          raise TypeError(
              "update должна быть функцией: def update(Time):"
          )

        self.execution_namespace = namespace
        self.update_function = update_function

        self._call_update(0.0)

        if (
            self.realtime_checkbox.isChecked()
            and self.update_function is not None
        ):
          self._start_playback()

        else:
          self.clear_parameter_widgets()
          self.execution_status.setText("Готово")

      finally:
        if batch_render:
          self.viewport.end_update()

    except Exception:
      self._stop_playback()
      self.execution_status.setText("Ошибка выполнения")

      details = traceback.format_exc()
      self.execution_status.setToolTip(details)
      report_exception(
          f"Выполнение кода проекта «{self.project.get('name', '?')}»",
          sys.exc_info()
      )

  def _toggle_realtime(self, enabled):
    if enabled:
      self.execution_status.setText(
          "Режим реального времени включён"
      )
    else:
      self.execution_status.setText("Готово")

  def closeEvent(self, event):
    editor_sizes = self.main_splitter.sizes()

    if editor_sizes and editor_sizes[0] > 0:
      self.settings.set(
          editor_sizes[0],
          "general",
          "layout_sizes",
          "editor_width"
      )

    if self.parameters_container.isVisible():
      parameter_sizes = self.parameters_splitter.sizes()

      if parameter_sizes and parameter_sizes[0] > 0:
        self.settings.set(
            parameter_sizes[0],
            "general",
            "layout_sizes",
            "parameters_panel_width"
        )

    try:
      if not self.code_saved:
        self.store.save_code(self.project, self.editor.toPlainText())
        self.code_saved = True
    except Exception as error:
      answer = QMessageBox.warning(
          self,
          "Ошибка сохранения",
          f"Не удалось сохранить код проекта:\\n{error}\\n\\nЗакрыть окно без сохранения?",
          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
          QMessageBox.StandardButton.No
      )
      if answer != QMessageBox.StandardButton.Yes:
        event.ignore()
        return

    self._stop_playback()
    app = QApplication.instance()
    if app is not None:
      app.removeEventFilter(self._ui_event_filter)
    super().closeEvent(event)

  def _on_run_button(self):
    if self.is_running or self.is_paused:
      self._stop_playback()

      self.clear_parameter_widgets()
      self.execution_namespace = {}
      self.update_function = None
      self.parameter_api = None

      self.execution_status.setText("Остановлено")

    else:
      self._execute_code()

  def _start_playback(self):
    self.time_base = self.current_time

    self.clock.start()
    self._fps_clock.restart()
    self._fps_frames = 0
    self._set_simulation_stats(0)
    self.frame_timer.start()

    self.is_running = True
    self.is_paused = False

    self.pause_button.setEnabled(True)
    self.pause_button.setText("Ⅱ Пауза")

    self._set_run_button(True)

    self.execution_status.setText("Воспроизведение")

  def _on_frame(self):
    if not self.is_running or self.update_function is None:
      return

    elapsed = self.clock.nsecsElapsed() / 1_000_000_000
    current_time = self.time_base + elapsed

    try:
      self._call_update(current_time)
      self._fps_frames += 1

      fps_elapsed = self._fps_clock.elapsed()
      if fps_elapsed >= 500:
        fps = self._fps_frames * 1000.0 / fps_elapsed
        self._set_simulation_stats(fps)
        self._fps_frames = 0
        self._fps_clock.restart()

    except Exception:
      self._stop_playback()

      self.execution_status.setText("Ошибка в update(Time)")

      details = traceback.format_exc()
      self.execution_status.setToolTip(details)
      report_exception(
          f"Обновление кадра проекта «{self.project.get('name', '?')}»",
          sys.exc_info()
      )

  def _set_simulation_stats(self, fps):
    self.simulation_stats_label.setText(
        f"FPS: {fps:.0f} | Время: {self.current_time:.2f} с"
    )

  def _toggle_pause(self):
    if self.update_function is None:
      return

    if self.is_running:
      elapsed = self.clock.nsecsElapsed() / 1_000_000_000

      self.current_time = self.time_base + elapsed

      self.frame_timer.stop()
      self.is_running = False
      self.is_paused = True
      self._set_simulation_stats(0)

      self.pause_button.setText("▶ Продолжить")

      self.execution_status.setText("Пауза")

    elif self.is_paused:
      self.time_base = self.current_time

      self.clock.start()
      self._fps_clock.restart()
      self._fps_frames = 0
      self._set_simulation_stats(0)
      self.frame_timer.start()

      self.is_running = True
      self.is_paused = False

      self.pause_button.setText("Ⅱ Пауза")

      self.execution_status.setText("Воспроизведение")

  def _stop_playback(self):
    if self.is_running:
      elapsed = self.clock.nsecsElapsed() / 1_000_000_000
      self.current_time = self.time_base + elapsed

    self.frame_timer.stop()

    self.is_running = False
    self.is_paused = False
    self._set_simulation_stats(0)

    self.pause_button.setEnabled(False)
    self.pause_button.setText("Ⅱ Пауза")

    self._set_run_button(False)

  def _set_run_button(self, running):
    if running:
      self.run_button.setText("Стоп")

      self.run_button.setStyleSheet("""
            QPushButton {
                background-color: #278b45;
                color: white;
                font-weight: bold;
            }
        """)

    else:
      self.run_button.setText("Выполнить код")
      self.run_button.setStyleSheet("")

  def _on_realtime_toggled(self, enabled):
    if not enabled:
      if self.is_running or self.is_paused:
        self._stop_playback()

      self.clear_parameter_widgets()
      self.execution_status.setText("Готово")

    else:
      self.execution_status.setText(
          "Режим реального времени включён"
      )

  def _call_update(self, value):
    self.current_time = float(value)
    self.execution_namespace["Time"] = self.current_time

    batch_render = hasattr(self.viewport, "begin_update")
    if batch_render:
      self.viewport.begin_update()

    try:
      if self.update_function is not None:
        self.update_function(self.current_time)

      self._update_scene()

    finally:
      if batch_render:
        self.viewport.end_update()

  def _on_parameter_changed(self, name, value):
    if not self.execution_namespace:
      return

    self.execution_namespace[name] = value

    if self.update_function is None:
      return

    try:
      self._call_update(self.current_time)

    except Exception:
      self._stop_playback()

      self.execution_status.setText(
          "Ошибка обновления параметра"
      )

      details = traceback.format_exc()
      self.execution_status.setToolTip(details)
      report_exception(
          f"Обновление параметра «{name}» проекта "
          f"«{self.project.get('name', '?')}»",
          sys.exc_info()
      )

  def _create_geometry(self, geometry_class, *args, **kwargs):
    obj = geometry_class(
        *args,
        **kwargs,
        draw_callback=lambda item: self.viewport.add_object(item),
        update_callback=lambda item, handle: self.viewport.update_object(
            item, handle
        )
    )
    self.geometry_objects.append(obj)
    return obj


  def _clear_scene(self):
    self.geometry_objects.clear()
    self.viewport.clear_scene()

  def _update_scene(self):
    pass

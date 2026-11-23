import io
import traceback

from contextlib import redirect_stdout, redirect_stderr

from PySide6.QtCore import Qt, QTimer, QElapsedTimer
from PySide6.QtWidgets import (
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
    QSlider,
    QFrame
)

from .settings import apply_theme
from .geometry import Square, Cube
from .rendering import Viewport2D, Viewport3D


class ParameterAPI:

  def __init__(self, window, create_widgets=False):
    self.window = window
    self.values = {}
    self.create_widgets = create_widgets

  def _validate_name(self, name):
    if not isinstance(name, str) or not name.isidentifier():
      raise ValueError(
          f"Некорректное имя параметра: {name}"
      )

  def slider(
      self,
      name,
      min=0,
      max=100,
      value=50,
      step=1,
      label=None
  ):
    self._validate_name(name)

    if step <= 0 or max <= min:
      raise ValueError(
          f"Некорректный диапазон ползунка: {name}"
      )

    count = round((max - min) / step)

    if count <= 0:
      raise ValueError(
          f"Некорректный диапазон ползунка: {name}"
      )

    max_value = min + count * step
    value = max_value if value > max_value else value
    value = min if value < min else value

    index = round((value - min) / step)
    initial_value = min + index * step

    self.values[name] = initial_value

    if self.create_widgets:
      container = QWidget()
      layout = QVBoxLayout(container)
      layout.setContentsMargins(0, 4, 0, 4)

      title = QLabel(label or name)
      value_label = QLabel(f"{initial_value:g}")

      header = QHBoxLayout()
      header.addWidget(title)
      header.addStretch()
      header.addWidget(value_label)

      slider = QSlider(Qt.Horizontal)
      slider.setRange(0, count)
      slider.setValue(index)

      layout.addLayout(header)
      layout.addWidget(slider)

      self.window.add_parameter_widget(container)

      def on_value_changed(index):
        current_value = min + index * step

        value_label.setText(f"{current_value:g}")
        self.values[name] = current_value

        self.window._on_parameter_changed(
            name,
            current_value
        )

      slider.valueChanged.connect(on_value_changed)

    return initial_value

  def checkbox(self, name, value=False, label=None):
    if not name.isidentifier():
      raise ValueError(
          f"Имя параметра должно быть Python-идентификатором: {name}"
      )

    self.values[name] = value

    if self.create_widgets:
      checkbox = QCheckBox(label or name)
      checkbox.setChecked(value)

      self.window.add_parameter_widget(checkbox)

      def on_toggled(checked):
        self.values[name] = checked

        self.window._on_parameter_changed(
            name,
            checked
        )

      checkbox.toggled.connect(on_toggled)

    return value

  def _on_checkbox_changed(self, name, value):
    self.values[name] = value

    self.window._on_parameter_changed(
        name,
        value
    )


class ProjectWindow(QMainWindow):

  def __init__(self, project, settings):
    super().__init__()

    self.project = project
    self.settings = settings

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

    central = QWidget()
    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(8, 8, 8, 8)
    root_layout.setSpacing(8)

    self._build_toolbar(root_layout)
    self._build_workspace(root_layout)

    self.setCentralWidget(central)

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

  def _build_toolbar(self, layout):
    toolbar = QHBoxLayout()
    toolbar.setSpacing(8)

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

    self.execution_status = QLabel("Готово")

    toolbar.addWidget(self.run_button)
    toolbar.addWidget(self.pause_button)
    toolbar.addWidget(self.realtime_checkbox)
    toolbar.addStretch()
    toolbar.addWidget(self.execution_status)

    layout.addLayout(toolbar)

    self.frame_timer = QTimer(self)
    self.frame_timer.setInterval(16)
    self.frame_timer.timeout.connect(self._on_frame)

    self.clock = QElapsedTimer()

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

    title = QLabel("Код")
    title.setObjectName("sectionTitle")
    editor_layout.addWidget(title)

    self.editor = QPlainTextEdit()
    self.editor.setPlaceholderText(
        "Введите код здесь..."
    )
    self.editor.setPlainText("""import math

speed = ui.slider(
    "speed",
    label="Скорость",
    min=0,
    max=10,
    value=2,
    step=0.1
)

radius = ui.slider(
    "radius",
    label="Радиус",
    min=1,
    max=10,
    value=5,
    step=0.5
)

amplitude = ui.slider(
    "amplitude",
    label="Амплитуда",
    min=0,
    max=5,
    value=2,
    step=0.1
)

show_grid = ui.checkbox(
    "show_grid",
    label="Показывать сетку",
    value=True
)

show_circle = ui.checkbox(
    "show_circle",
    label="Показывать окружность",
    value=True
)

show_wave = ui.checkbox(
    "show_wave",
    label="Показывать волну",
    value=True
)


def update(Time):
    angle = Time * speed

    x = math.cos(angle) * radius
    y = math.sin(angle) * radius

    wave = math.sin(angle) * amplitude

    print(
        f"Время: {Time:7.2f} | "
        f"Угол: {angle:7.2f} | "
        f"X: {x:7.2f} | "
        f"Y: {y:7.2f}"
    )

    if show_grid:
        print("Сетка: включена")

    if show_circle:
        print("Окружность: включена")

    if show_wave:
        print(f"Волна: {wave:.2f}")

    print("-" * 60)
""")

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
      self.viewport = Viewport2D(self.scene_container)
    else:
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
    while self.parameters_content.count():
      item = self.parameters_content.takeAt(0)

      widget = item.widget()
      if widget is not None:
        widget.deleteLater()

    self.parameters_container.hide()

  def _execute_code(self):
    self._stop_playback()
    self.clear_parameter_widgets()
    self._clear_scene()

    source = self.editor.toPlainText()

    self.execution_status.setText("Выполнение...")
    self._set_run_button(False)

    self.current_time = 0.0
    self.time_base = 0.0

    self.parameter_api = ParameterAPI(
        self,
        create_widgets=self.realtime_checkbox.isChecked()
    )

    namespace = {
        "__name__": "__main__",
        "ui": self.parameter_api,
        "New_SQUARE": self._new_square,
        "New_CUBE": self._new_cube
    }

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

    except Exception as error:
      self._stop_playback()
      self.execution_status.setText("Ошибка выполнения")

      self.execution_status.setToolTip(traceback.format_exc())

      print(traceback.format_exc())

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

    self._stop_playback()
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

      self.execution_status.setText(
          f"Воспроизведение | {self.current_time:.2f} с"
      )

    except Exception:
      self._stop_playback()

      self.execution_status.setText("Ошибка в update(Time)")

      self.scene_label.setText(
          traceback.format_exc()
      )

      print(traceback.format_exc())

  def _toggle_pause(self):
    if self.update_function is None:
      return

    if self.is_running:
      elapsed = self.clock.nsecsElapsed() / 1_000_000_000

      self.current_time = self.time_base + elapsed

      self.frame_timer.stop()
      self.is_running = False
      self.is_paused = True

      self.pause_button.setText("▶ Продолжить")

      self.execution_status.setText("Пауза")

    elif self.is_paused:
      self.time_base = self.current_time

      self.clock.start()
      self.frame_timer.start()

      self.is_running = True
      self.is_paused = False

      self.pause_button.setText("Ⅱ Пауза")

      self.execution_status.setText("Воспроизведение")

  def _stop_playback(self):
    self.frame_timer.stop()

    self.is_running = False
    self.is_paused = False

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

    if self.update_function is not None:
      self.update_function(self.current_time)

    self._update_scene()

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

      self.scene_label.setText(
          traceback.format_exc()
      )

      print(traceback.format_exc())

  def _new_square(self, **kwargs):
    if self.project["mode"] != "2D":
      raise RuntimeError("New_SQUARE доступен только в 2D-проекте.")
    obj = Square(
        **kwargs,
        draw_callback=lambda item: self.viewport.add_object(item),
        update_callback=lambda item, handle: self.viewport.update_object(item, handle)
    )
    self.geometry_objects.append(obj)
    return obj

  def _new_cube(self, **kwargs):
    if self.project["mode"] != "3D":
      raise RuntimeError("New_CUBE доступен только в 3D-проекте.")
    obj = Cube(
        **kwargs,
        draw_callback=lambda item: self.viewport.add_object(item),
        update_callback=lambda item, handle: self.viewport.update_object(item, handle)
    )
    self.geometry_objects.append(obj)
    return obj

  def _clear_scene(self):
    self.geometry_objects.clear()
    if self.project["mode"] == "2D":
      self.viewport.graph.clear()
    else:
      self.viewport.plotter.clear()
      self.viewport.plotter.set_background("#20232b")
      self.viewport.plotter.add_axes()
      self.viewport.plotter.show_grid(color="#777777")
      self.viewport.plotter.view_isometric()

  def _update_scene(self):
    pass

import traceback
import numpy as np
import pyvista as pv
import pyqtgraph as pg

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QLabel,
    QSplitter,
    QStackedWidget,
    QComboBox,
    QMessageBox
)

from PySide6.QtCore import Qt
from pyvistaqt import QtInteractor
from code_editor import CodeEditor


class InterfaceMixin:

  def open_options(self):
    QMessageBox.information(
        self,
        "Опции",
        "Окно настроек пока не реализовано."
    )

  def _create_interface(self):

    central = QWidget()
    self.setCentralWidget(central)

    main_layout = QVBoxLayout(central)
    main_layout.setContentsMargins(5, 5, 5, 5)
    main_layout.setSpacing(4)

    self.project_combo = QComboBox()
    self.project_combo.setEditable(True)
    self.project_combo.setMinimumWidth(220)
    self.project_combo.setPlaceholderText("Новый проект")

    self.project_combo.activated.connect(
        self.on_project_selected
    )

    self.project_combo.lineEdit().editingFinished.connect(
        self.on_project_name_edited
    )

    self.new_project_button = QPushButton("Новый проект")
    self.new_project_button.clicked.connect(self.create_new_project)

    self.options_button = QPushButton("Опции")
    self.options_button.clicked.connect(self.open_options)

    self.delete_project_button = QPushButton("Удалить")
    self.delete_project_button.clicked.connect(self.delete_current_project)

    project_toolbar = QHBoxLayout()

    self.help_button = QPushButton("Справка")
    self.help_button.clicked.connect(self.open_help)

    project_toolbar.addWidget(self.new_project_button)
    project_toolbar.addWidget(QLabel("Проект:"))
    project_toolbar.addWidget(self.project_combo)
    project_toolbar.addWidget(self.options_button)
    project_toolbar.addWidget(self.delete_project_button)

    project_toolbar.addStretch()

    project_toolbar.addWidget(self.help_button)

    main_layout.addLayout(project_toolbar)

    toolbar = QHBoxLayout()

    self.btn_run = QPushButton("▶ Выполнить")
    self.btn_run.setFixedHeight(32)
    self.btn_run.clicked.connect(self.run_code)

    self.btn_pause = QPushButton("Ⅱ Пауза")
    self.btn_pause.setFixedHeight(32)
    self.btn_pause.setEnabled(False)
    self.btn_pause.clicked.connect(self.toggle_pause)

    self.btn_mode = QPushButton("Перейти в 3D")
    self.btn_mode.setFixedHeight(32)
    self.btn_mode.clicked.connect(self.toggle_mode)

    self.status = QLabel("Готово")
    self.time_label = QLabel("Time: 0.000 s")

    toolbar.addWidget(self.btn_run)
    toolbar.addWidget(self.btn_pause)
    toolbar.addWidget(self.btn_mode)
    toolbar.addWidget(self.status)

    toolbar.addStretch()
    toolbar.addWidget(self.time_label)

    main_layout.addLayout(toolbar)

    splitter = QSplitter(Qt.Orientation.Horizontal)

    self.editor = CodeEditor()

    splitter.addWidget(self.editor)

    self.view_stack = QStackedWidget()

    # 2D viewport
    self.graph = pg.PlotWidget()
    self._configure_2d_graph()

    # 3D viewport
    self.plotter = QtInteractor(self)
    self.plotter.set_background("#20232b")

    self.plotter.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    self.plotter.installEventFilter(self)

    self.view_stack.addWidget(self.graph)
    self.view_stack.addWidget(self.plotter)

    splitter.addWidget(self.view_stack)

    splitter.setSizes([450, 950])
    splitter.setMinimumHeight(300)

    main_layout.addWidget(splitter, 1)

  def _show_code_error(self, error):

    line = None

    # Синтаксическая ошибка
    if isinstance(error, SyntaxError):
      line = error.lineno

    # Ошибка во время выполнения
    else:
      frames = traceback.extract_tb(error.__traceback__)

      for frame in reversed(frames):
        if frame.filename == "<string>":
          line = frame.lineno
          break

    self.editor.set_error_line(line)

  def _configure_2d_graph(self):

    self.graph.setBackground("#20232b")

    self.graph.setXRange(-20, 20)
    self.graph.setYRange(-20, 20)

    self.graph.setAspectLocked(True)
    self.graph.showGrid(x=True, y=True)

    self.graph.setLabel("bottom", "X")
    self.graph.setLabel("left", "Y")

  def _create_floor(self, size=100, step=5):

    half = size / 2

    points = []
    lines = []

    def add_line(start, end):

      index = len(points)

      points.append(start)
      points.append(end)

      lines.extend([2, index, index + 1])

    count = int(size / step)

    for i in range(count + 1):

      pos = -half + i * step

      # Линии вдоль X
      add_line(
          (-half, 0, pos),
          (half, 0, pos)
      )

      # Линии вдоль Z
      add_line(
          (pos, 0, -half),
          (pos, 0, half)
      )

    grid = pv.PolyData(
        np.array(points, dtype=float),
        lines=np.array(lines, dtype=np.int64)
    )

    self.plotter.add_mesh(
        grid,
        color="#414956",
        line_width=1,
        lighting=False,
        name="world_grid"
    )

    # Центральная ось X
    self.plotter.add_mesh(
        pv.Line(
            (-half, 0, 0),
            (half, 0, 0)
        ),
        color="#d65b5b",
        line_width=2,
        lighting=False
    )

    # Центральная ось Z
    self.plotter.add_mesh(
        pv.Line(
            (0, 0, -half),
            (0, 0, half)
        ),
        color="#5b91d6",
        line_width=2,
        lighting=False
    )

    # Центральная ось Y
    self.plotter.add_mesh(
        pv.Line(
            (0, -half, 0),
            (0, half, 0)
        ),
        color="#65c878",
        line_width=2,
        lighting=False
    )

  def _configure_3d_scene(self):

    self.plotter.set_background("#20232b")

    # Оси в углу экрана
    self.plotter.add_axes()

    # Сетка пола в плоскости XZ, Y = 0
    self._create_floor(
        size=1000,
        step=10
    )
    if not self._camera_initialized:
      self.plotter.camera_position = "iso"
      self.plotter.camera.SetViewUp(0, 1, 0)
      self.plotter.camera.OrthogonalizeViewUp()

    self._update_camera()

  def _reset_3d_camera(self):

    camera = self.plotter.camera

    camera.SetFocalPoint(0, 0, 0)

    camera.SetPosition(22, 16.5, 22)

    camera.SetViewUp(0, 1, 0)
    camera.OrthogonalizeViewUp()

    self._update_camera()

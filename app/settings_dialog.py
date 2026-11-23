from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QDialog,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget
)

from .settings import DEFAULT_SETTINGS


class SettingsDialog(QDialog):
  settings_applied = Signal()

  def __init__(self, settings, parent=None):
    super().__init__(parent)
    self.settings = settings
    self.setWindowTitle("Настройки Geometry Playground")
    self.resize(620, 440)

    root = QVBoxLayout(self)
    self.tabs = QTabWidget()
    root.addWidget(self.tabs)

    self._build_general_tab()
    self._build_manager_tab()
    self._build_project_tab("2D", "project_2d")
    self._build_project_tab("3D", "project_3d")

    buttons_layout = QHBoxLayout()
    buttons_layout.addStretch()

    self.apply_button = QPushButton("Применить")
    self.reset_button = QPushButton("Сбросить")
    self.cancel_button = QPushButton("Отмена")

    self.apply_button.clicked.connect(self._apply)
    self.reset_button.clicked.connect(self._reset)
    self.cancel_button.clicked.connect(self.reject)

    buttons_layout.addWidget(self.apply_button)
    buttons_layout.addWidget(self.reset_button)
    buttons_layout.addWidget(self.cancel_button)
    root.addLayout(buttons_layout)

  def _build_general_tab(self):
    page = QWidget()
    layout = QVBoxLayout(page)
    form = QFormLayout()

    self.color_buttons = {}
    colors = self.settings.get("general", "colors", default={})
    color_labels = {
        "background": "Цвет фона",
        "text": "Цвет текста",
        "accent": "Акцентный цвет"
    }

    for key, label in color_labels.items():
      button = QPushButton(colors.get(key, "#ffffff"))
      button.setProperty("color_key", key)
      button.clicked.connect(
          lambda checked=False, b=button: self._choose_color(b)
      )
      self._set_color_button(button, button.text())
      self.color_buttons[key] = button
      form.addRow(label, button)

    self.manager_width, self.manager_height = self._size_inputs(
        "manager", "Размер окна менеджера", form
    )
    self.project2d_width, self.project2d_height = self._size_inputs(
        "project_2d", "Размер окна 2D-проекта", form
    )
    self.project3d_width, self.project3d_height = self._size_inputs(
        "project_3d", "Размер окна 3D-проекта", form
    )

    layout_sizes = self.settings.get(
        "general", "layout_sizes", default={}
    )

    self.editor_width = QSpinBox()
    self.editor_width.setRange(250, 1600)
    self.editor_width.setValue(
        layout_sizes.get("editor_width", 450)
    )
    form.addRow("Ширина редактора", self.editor_width)

    self.editor_font_size = QSpinBox()
    self.editor_font_size.setRange(6, 48)
    self.editor_font_size.setValue(
        self.settings.get("general", "editor_font_size", default=16)
    )
    form.addRow("Размер текста в редакторе", self.editor_font_size)

    self.parameters_panel_width = QSpinBox()
    self.parameters_panel_width.setRange(200, 1600)
    self.parameters_panel_width.setValue(
        layout_sizes.get("parameters_panel_width", 450)
    )
    form.addRow(
        "Ширина панели параметров",
        self.parameters_panel_width
    )

    layout.addLayout(form)
    layout.addStretch()
    self.tabs.addTab(page, "Общие")

  def _size_inputs(self, key, label, form):
    size = self.settings.get(
        "general", "window_sizes", key, default=[900, 600]
    )
    width = QSpinBox()
    height = QSpinBox()
    for spin in (width, height):
      spin.setRange(400, 4000)
    width.setValue(int(size[0]))
    height.setValue(int(size[1]))

    row = QWidget()
    row_layout = QHBoxLayout(row)
    row_layout.setContentsMargins(0, 0, 0, 0)
    row_layout.addWidget(QLabel("Ширина"))
    row_layout.addWidget(width)
    row_layout.addSpacing(12)
    row_layout.addWidget(QLabel("Высота"))
    row_layout.addWidget(height)
    form.addRow(label, row)
    return width, height

  def _choose_color(self, button):
    color = QColorDialog.getColor(QColor(button.text()), self)
    if color.isValid():
      self._set_color_button(button, color.name())

  @staticmethod
  def _set_color_button(button, color):
    button.setText(color)
    button.setStyleSheet(
        f"background-color: {color}; color: "
        f"{'black' if QColor(color).lightness() > 150 else 'white'};"
    )

  def _build_manager_tab(self):
    page = QWidget()
    layout = QVBoxLayout(page)
    form = QFormLayout()

    self.folder_edit = QLineEdit(str(self.settings.projects_folder or ""))
    self.folder_edit.setReadOnly(True)
    browse = QPushButton("Выбрать…")
    browse.clicked.connect(self._browse_folder)

    folder_row = QWidget()
    folder_layout = QHBoxLayout(folder_row)
    folder_layout.setContentsMargins(0, 0, 0, 0)
    folder_layout.addWidget(self.folder_edit, 1)
    folder_layout.addWidget(browse)
    form.addRow("Папка проектов", folder_row)

    self.close_on_open = QCheckBox(
        "Закрывать менеджер при открытии проекта"
    )
    self.close_on_open.setChecked(
        self.settings.get("manager", "close_on_open", default=False)
    )

    layout.addLayout(form)
    layout.addWidget(self.close_on_open)
    layout.addStretch()
    self.tabs.addTab(page, "Менеджер")

  def _browse_folder(self):
    start = self.folder_edit.text() or str(Path.home())
    folder = QFileDialog.getExistingDirectory(
        self, "Папка проектов", start
    )
    if folder:
      self.folder_edit.setText(folder)

  def _build_project_tab(self, title, key):
    page = QWidget()
    layout = QVBoxLayout(page)
    note = QLabel(
        f"Настройки режима {title} будут добавлены на следующем этапе."
    )
    note.setWordWrap(True)
    note.setAlignment(
        Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft
    )
    layout.addWidget(note)
    layout.addStretch()
    self.tabs.addTab(page, title)

  def _apply(self):
    colors = {
        key: button.text()
        for key, button in self.color_buttons.items()
    }
    self.settings.set(colors, "general", "colors")
    self.settings.set(
        {
            "manager": [
                self.manager_width.value(),
                self.manager_height.value()
            ],
            "project_2d": [
                self.project2d_width.value(),
                self.project2d_height.value()
            ],
            "project_3d": [
                self.project3d_width.value(),
                self.project3d_height.value()
            ],

        },
        "general", "window_sizes"
    )
    self.settings.set(
        {
            "editor_width": self.editor_width.value(),
            "editor_font_size": self.editor_font_size.value(),
            "parameters_panel_width": self.parameters_panel_width.value()
        },
        "general", "layout_sizes"
    )
    self.settings.set(
        self.close_on_open.isChecked(), "manager", "close_on_open"
    )

    folder = self.folder_edit.text().strip()
    self.settings.projects_folder = folder or None
    self.settings_applied.emit()

  def _reset(self):
    defaults = DEFAULT_SETTINGS

    for key, button in self.color_buttons.items():
      self._set_color_button(
          button, defaults["general"]["colors"][key]
      )

    sizes = defaults["general"]["window_sizes"]
    self.manager_width.setValue(sizes["manager"][0])
    self.manager_height.setValue(sizes["manager"][1])
    self.project2d_width.setValue(sizes["project_2d"][0])
    self.project2d_height.setValue(sizes["project_2d"][1])
    self.project3d_width.setValue(sizes["project_3d"][0])
    self.project3d_height.setValue(sizes["project_3d"][1])
    self.close_on_open.setChecked(
        defaults["manager"]["close_on_open"]
    )
    layout_sizes = defaults["general"]["layout_sizes"]
    self.editor_width.setValue(layout_sizes["editor_width"])
    self.parameters_panel_width.setValue(
        layout_sizes["parameters_panel_width"]
    )
    self.editor_font_size.setValue(
        layout_sizes.get("editor_font_size", 16)
    )

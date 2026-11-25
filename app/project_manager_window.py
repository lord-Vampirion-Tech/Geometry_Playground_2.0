from pathlib import Path
import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget
)

from .project_store import ProjectStore
from .settings import AppSettings, apply_theme
from .settings_dialog import SettingsDialog
from .crash_handler import report_exception, set_crash_context


class ProjectManagerWindow(QMainWindow):
  def __init__(self):
    super().__init__()

    self.settings = AppSettings()
    self.store = None
    self.project_windows = []

    self.setWindowTitle("Geometry Playground 2.0")
    manager_size = self.settings.get(
        "general", "window_sizes", "manager", default=[820, 520]
    )
    self.resize(int(manager_size[0]), int(manager_size[1]))

    self._build_interface()
    apply_theme(self, self.settings)

    folder = self.settings.projects_folder
    folder.mkdir(parents=True, exist_ok=True)
    self._set_projects_folder(folder)

  def _build_interface(self):
    central = QWidget()
    root_layout = QVBoxLayout(central)
    root_layout.setContentsMargins(14, 12, 14, 12)
    root_layout.setSpacing(10)

    self.toolbar = QWidget()
    toolbar = QHBoxLayout(self.toolbar)
    toolbar.setContentsMargins(0, 0, 0, 0)

    self.create_2d_button = QPushButton("Создать 2D проект")
    self.create_3d_button = QPushButton("Создать 3D проект")
    self.open_button = QPushButton("Открыть выбранный")
    self.delete_button = QPushButton("Удалить выбранный")
    self.settings_button = QPushButton("Настройки")

    self.create_2d_button.clicked.connect(lambda: self.create_project("2D"))
    self.create_3d_button.clicked.connect(lambda: self.create_project("3D"))
    self.open_button.clicked.connect(self.open_selected_project)
    self.delete_button.clicked.connect(self.delete_selected_project)
    self.settings_button.clicked.connect(self.open_settings)

    for button in (
        self.create_2d_button,
        self.create_3d_button,
        self.open_button,
        self.delete_button
    ):
      toolbar.addWidget(button)

    toolbar.addStretch()
    toolbar.addWidget(self.settings_button)
    root_layout.addWidget(self.toolbar)

    self.stack = QStackedWidget()

    self.empty_page = QWidget()
    empty_layout = QHBoxLayout(self.empty_page)
    empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
    empty_layout.setSpacing(16)

    self.empty_2d_button = QPushButton("Создать 2D проект")
    self.empty_3d_button = QPushButton("Создать 3D проект")
    for button in (self.empty_2d_button, self.empty_3d_button):
      button.setMinimumSize(190, 48)

    self.empty_2d_button.clicked.connect(lambda: self.create_project("2D"))
    self.empty_3d_button.clicked.connect(lambda: self.create_project("3D"))
    empty_layout.addWidget(self.empty_2d_button)
    empty_layout.addWidget(self.empty_3d_button)

    self.table = QTableWidget(0, 4)
    self.table.setHorizontalHeaderLabels([
        "Название", "Тип", "Дата создания", "Дата изменения"
    ])
    self.table.setSelectionBehavior(
        QAbstractItemView.SelectionBehavior.SelectRows
    )
    self.table.setSelectionMode(
        QAbstractItemView.SelectionMode.SingleSelection
    )
    self.table.setEditTriggers(
        QAbstractItemView.EditTrigger.NoEditTriggers
    )
    self.table.verticalHeader().setVisible(False)
    self.table.horizontalHeader().setStretchLastSection(True)
    self.table.doubleClicked.connect(self.open_selected_project)

    self.stack.addWidget(self.empty_page)
    self.stack.addWidget(self.table)
    root_layout.addWidget(self.stack, 1)

    self.folder_label = QLabel()
    self.folder_label.setTextInteractionFlags(
        Qt.TextInteractionFlag.TextSelectableByMouse
    )
    self.folder_label.setStyleSheet("color: #888;")
    root_layout.addWidget(self.folder_label)

    self.setCentralWidget(central)

  def _show_empty_state(self):
    self.toolbar.hide()
    self.folder_label.hide()
    self.stack.setCurrentWidget(self.empty_page)

  def _set_projects_folder(self, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    self.settings.projects_folder = folder
    self.store = ProjectStore(folder)
    self.folder_label.setText(f"Папка проектов: {folder}")
    self.refresh_projects()

  def refresh_projects(self):
    if self.store is None:
      self._show_empty_state()
      return

    projects = self.store.list_projects()
    self.table.setRowCount(0)

    for project in projects:
      row = self.table.rowCount()
      self.table.insertRow(row)

      values = [
          project.get("name", "Без названия"),
          project.get("mode", "?"),
          project.get("created_at", "").replace("T", " "),
          project.get("modified_at", "").replace("T", " ")
      ]

      for column, value in enumerate(values):
        item = QTableWidgetItem(value)
        if column == 0:
          item.setData(Qt.ItemDataRole.UserRole, project["id"])
        self.table.setItem(row, column, item)

    has_projects = bool(projects)
    self.toolbar.setVisible(has_projects)
    self.folder_label.setVisible(has_projects)
    self.stack.setCurrentWidget(
        self.table if has_projects else self.empty_page)

  def _selected_project(self):
    if self.store is None:
      return None

    row = self.table.currentRow()
    if row < 0:
      return None

    item = self.table.item(row, 0)
    if item is None:
      return None

    project_id = item.data(Qt.ItemDataRole.UserRole)
    return next(
        (project for project in self.store.list_projects()
         if project.get("id") == project_id),
        None
    )

  def create_project(self, mode):
    name, accepted = QInputDialog.getText(
        self, f"Создание {mode} проекта", "Название проекта:"
    )
    if not accepted:
      return

    name = name.strip()
    if not name:
      QMessageBox.warning(self, "Название проекта",
                          "Введите название проекта.")
      return

    if self.store is None:
      folder = QFileDialog.getExistingDirectory(
          self,
          "Выберите папку для сохранения проектов",
          str(Path.home() / "Documents")
      )
      if not folder:
        return
      self._set_projects_folder(folder)

    try:
      self.store.create_project(name, mode)
      self.refresh_projects()
    except Exception as error:
      QMessageBox.critical(self, "Ошибка", str(error))

  def open_settings(self):
    dialog = SettingsDialog(self.settings, self)
    dialog.settings_applied.connect(self._apply_settings)
    dialog.exec()

  def _apply_settings(self):
    apply_theme(self, self.settings)

    folder = self.settings.projects_folder
    if folder is not None:
      self._set_projects_folder(folder)

    manager_size = self.settings.get(
        "general", "window_sizes", "manager", default=[820, 520]
    )
    self.resize(int(manager_size[0]), int(manager_size[1]))

  def open_selected_project(self):
    project = None
    try:
      set_crash_context("Получение выбранного проекта")
      project = self._selected_project()
      if project is None:
        QMessageBox.information(
            self, "Проект не выбран", "Сначала выберите проект в списке."
        )
        return

      set_crash_context(
          f"Открытие проекта «{project.get('name', '?')}» "
          f"({project.get('mode', '?')}): создание окна"
      )
      from .project_window import ProjectWindow
      window = ProjectWindow(project, self.settings)
      close_manager = self.settings.get(
          "manager", "close_on_open", default=False
      )
      window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

      set_crash_context(
          f"Открытие проекта «{project.get('name', '?')}»: отображение окна"
      )
      self.project_windows.append(window)
      window.destroyed.connect(
          lambda: self._on_project_window_destroyed(window)
      )
      window.show()

      if close_manager:
        self.hide()

    except Exception:
      report_exception(
          f"Открытие проекта «{project.get('name', '?') if isinstance(project, dict) else '?'}»",
          sys.exc_info()
      )

  def _on_project_window_destroyed(self, window):
    self._remove_project_window(window)
    if not self.isVisible():
      self.show()

  def _remove_project_window(self, window):
    if window in self.project_windows:
      self.project_windows.remove(window)

  def delete_selected_project(self):
    project = self._selected_project()
    if project is None:
      QMessageBox.information(
          self, "Проект не выбран", "Сначала выберите проект в списке."
      )
      return

    answer = QMessageBox.question(
        self,
        "Удаление проекта",
        f"Удалить проект «{project['name']}» без возможности восстановления?",
        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        QMessageBox.StandardButton.No
    )
    if answer != QMessageBox.StandardButton.Yes:
      return

    try:
      self.store.delete_project(project)
      self.refresh_projects()
    except Exception as error:
      QMessageBox.critical(self, "Ошибка", str(error))

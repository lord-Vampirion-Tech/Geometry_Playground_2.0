
from pathlib import Path
import tempfile

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QFileDialog,
    QMessageBox,
    QDialogButtonBox,
)


class SetupDialog(QDialog):

  def __init__(self, storage_folder="", theme="system", parent=None):
    super().__init__(parent)

    self.setWindowTitle("Настройка Geometry Playground")
    self.setMinimumWidth(480)
    self.setModal(True)

    layout = QVBoxLayout(self)
    layout.setSpacing(12)

    title = QLabel("Первоначальная настройка")
    title.setStyleSheet("font-size: 18px; font-weight: bold;")

    description = QLabel(
        "Выберите папку, в которой будут храниться ваши проекты, "
        "и базовую тему оформления."
    )
    description.setWordWrap(True)

    layout.addWidget(title)
    layout.addWidget(description)

    # Папка проектов
    layout.addWidget(QLabel("Папка для проектов:"))

    folder_layout = QHBoxLayout()

    self.folder_input = QLineEdit()
    self.folder_input.setPlaceholderText("Выберите папку...")

    self.browse_button = QPushButton("Обзор...")
    self.browse_button.clicked.connect(self.choose_folder)

    folder_layout.addWidget(self.folder_input)
    folder_layout.addWidget(self.browse_button)

    layout.addLayout(folder_layout)

    if storage_folder:
      self.folder_input.setText(str(storage_folder))
    else:
      default_folder = Path.home() / "Documents" / "Geometry Playground"
      self.folder_input.setText(str(default_folder))

    # Тема
    layout.addWidget(QLabel("Тема оформления:"))

    self.theme_combo = QComboBox()
    self.theme_combo.addItem("Системная", "system")
    self.theme_combo.addItem("Тёмная", "dark")
    self.theme_combo.addItem("Светлая", "light")

    theme_index = self.theme_combo.findData(theme)

    if theme_index >= 0:
      self.theme_combo.setCurrentIndex(theme_index)

    layout.addWidget(self.theme_combo)

    # Кнопки
    self.buttons = QDialogButtonBox(
        QDialogButtonBox.StandardButton.Ok
        | QDialogButtonBox.StandardButton.Cancel
    )

    self.buttons.button(
        QDialogButtonBox.StandardButton.Ok
    ).setText("Продолжить")

    self.buttons.button(
        QDialogButtonBox.StandardButton.Cancel
    ).setText("Отмена")

    self.buttons.accepted.connect(self.validate_and_accept)
    self.buttons.rejected.connect(self.reject)

    layout.addWidget(self.buttons)

  def choose_folder(self):
    folder = QFileDialog.getExistingDirectory(
        self,
        "Выберите папку для проектов",
        self.folder_input.text()
    )

    if folder:
      self.folder_input.setText(folder)

  def validate_and_accept(self):
    folder_text = self.folder_input.text().strip()

    if not folder_text:
      QMessageBox.warning(
          self,
          "Не выбрана папка",
          "Укажите папку для хранения проектов."
      )
      return

    folder = Path(folder_text).expanduser()

    try:
      folder.mkdir(parents=True, exist_ok=True)

      if not folder.is_dir():
        raise OSError("Указанный путь не является папкой")

      # Проверяем, что в папку действительно можно записывать файлы.
      with tempfile.NamedTemporaryFile(
          dir=folder,
          prefix=".geometry_playground_test_",
          delete=True
      ):
        pass

    except OSError as error:
      QMessageBox.critical(
          self,
          "Ошибка доступа",
          f"Не удалось использовать выбранную папку:\n\n{error}"
      )
      return

    self.folder_input.setText(str(folder.resolve()))
    self.accept()

  def get_storage_folder(self):
    return self.folder_input.text().strip()

  def get_theme(self):
    return self.theme_combo.currentData()

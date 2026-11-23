from time import perf_counter

START_TIME = perf_counter()

def startup_checkpoint(name):
    elapsed = perf_counter() - START_TIME
    print(f"[STARTUP] {name}: {elapsed:.3f} сек.")

import sys
import tempfile

from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog

from settings import AppSettings
from setup_dialog import SetupDialog

from main.window import MainWindow
from PySide6.QtGui import QIcon

startup_checkpoint("Импорты")

def is_storage_available(folder):

  try:
    path = Path(folder)
    path.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(
        dir=path,
        delete=True
    ):
      pass

    return True

  except Exception:
    return False

def resource_path(relative_path):

    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)
    else:
        base_path = Path(__file__).resolve().parent

    return base_path / relative_path

if __name__ == "__main__":

  app = QApplication(sys.argv)
  startup_checkpoint("QApplication")
  app.setApplicationName("Geometry Playground")
  app.setOrganizationName("ZifTech")

  app_icon = QIcon(str(resource_path("assets/app.ico")))
  app.setWindowIcon(app_icon)

  settings = AppSettings()

  storage_folder = settings.get("storage_folder")
  theme = settings.get("theme") or "system"

  if not is_storage_available(storage_folder):

    dialog = SetupDialog(
        storage_folder=storage_folder,
        theme=theme
    )

    if dialog.exec() != QDialog.DialogCode.Accepted:
      sys.exit(0)

    storage_folder = dialog.get_storage_folder()
    theme = dialog.get_theme()

    settings.set_storage_folder(storage_folder)
    settings.set("theme", theme)

  window = MainWindow(settings)
  startup_checkpoint("MainWindow")
  window.show()
  startup_checkpoint("Окно показано")

  sys.exit(app.exec())

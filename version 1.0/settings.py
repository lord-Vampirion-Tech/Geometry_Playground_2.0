
import json
from pathlib import Path

from PySide6.QtCore import QStandardPaths


class AppSettings:

  DEFAULTS = {
      "storage_folder": "",
      "theme": "system",
      "font_family": "Consolas",
      "font_size": 12,
      "autosave_delay": 1000,
      "last_project_id": None
  }

  def __init__(self):

    config_folder = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        )
    )

    config_folder.mkdir(parents=True, exist_ok=True)

    self.path = config_folder / "settings.json"

    self.data = self.DEFAULTS.copy()

    self.load()

  def load(self):

    if not self.path.exists():
      return

    try:
      with self.path.open("r", encoding="utf-8") as file:
        saved = json.load(file)

      self.data.update(saved)

    except (OSError, json.JSONDecodeError):
      self.data = self.DEFAULTS.copy()

  def save(self):

    self.path.parent.mkdir(parents=True, exist_ok=True)

    with self.path.open("w", encoding="utf-8") as file:
      json.dump(
          self.data,
          file,
          indent=4,
          ensure_ascii=False
      )

  def get(self, key):
    return self.data.get(key)

  def set(self, key, value):

    self.data[key] = value
    self.save()

  def get_storage_folder(self):

    folder = self.get("storage_folder")

    return Path(folder) if folder else None

  def set_storage_folder(self, folder):

    self.set("storage_folder", str(Path(folder).resolve()))

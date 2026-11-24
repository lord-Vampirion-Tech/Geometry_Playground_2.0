import json
from pathlib import Path

from PySide6.QtGui import QColor

from PySide6.QtCore import QStandardPaths


DEFAULT_SETTINGS = {
    "general": {
        "colors": {
            "background": "#20232b",
            "text": "#e8eaf0",
            "accent": "#42a5f5"
        },
        "window_sizes": {
            "manager": [820, 520],
            "project_2d": [1100, 750],
            "project_3d": [1100, 750]
        },
        "layout_sizes": {
            "editor_width": 450,
            "parameters_panel_width": 450
        },
        "ui_groups": {
            "border_width": 5,
            "border_color": "#000000"
        }
    },
    "manager": {
        "close_on_open": False
    },
    "project_2d": {},
    "project_3d": {},
    "projects_folder": None
}


class AppSettings:
  def __init__(self):
    config_dir = Path(
        QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppConfigLocation
        )
    )
    config_dir.mkdir(parents=True, exist_ok=True)

    self.path = config_dir / "settings.json"
    loaded = self._load()
    self.data = self._merge_defaults(loaded)
    self.save()

  def _load(self):
    if not self.path.exists():
      return {}

    try:
      return json.loads(self.path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
      return {}

  @staticmethod
  def _merge_defaults(loaded):
    def merge(default, current):
      if not isinstance(default, dict):
        return current if current is not None else default

      result = dict(default)
      if isinstance(current, dict):
        for key, value in current.items():
          if key in result and isinstance(result[key], dict):
            result[key] = merge(result[key], value)
          else:
            result[key] = value
      return result

    return merge(DEFAULT_SETTINGS, loaded)

  def save(self):
    self.path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = self.path.with_suffix(".tmp")
    temporary_path.write_text(
        json.dumps(self.data, ensure_ascii=False, indent=4),
        encoding="utf-8"
    )
    temporary_path.replace(self.path)

  def get(self, *keys, default=None):
    value = self.data
    for key in keys:
      if not isinstance(value, dict) or key not in value:
        return default
      value = value[key]
    return value

  def set(self, value, *keys):
    target = self.data
    for key in keys[:-1]:
      target = target.setdefault(key, {})
    target[keys[-1]] = value
    self.save()

  @property
  def projects_folder(self):
    value = self.data.get("projects_folder")
    return Path(value) if value else None

  @projects_folder.setter
  def projects_folder(self, value):
    self.data["projects_folder"] = str(Path(value)) if value else None
    self.save()


def apply_theme(widget, settings):
  colors = settings.get("general", "colors", default={})
  background = colors.get("background", "#20232b")
  text = colors.get("text", "#e8eaf0")
  accent = colors.get("accent", "#42a5f5")
  header_background = QColor(background).lighter(108).name()

  widget.setStyleSheet(f"""
        QWidget {{
            background-color: {background};
            color: {text};
        }}
        QPushButton {{
            background-color: {accent};
            color: white;
            border: none;
            border-radius: 4px;
            padding: 7px 11px;
        }}
        QPushButton:hover {{
            border: 1px solid {text};
        }}
        QPushButton:disabled {{
            background-color: #555a64;
            color: #aaaaaa;
        }}
        QTableWidget, QLineEdit, QSpinBox, QTabWidget::pane {{
            background-color: {background};
            color: {text};
            border: 1px solid #555a64;
        }}
        QHeaderView::section {{
            background-color: {header_background};
            color: {text};
            padding: 5px;
            border: 1px solid #454b56;
        }}
    """)

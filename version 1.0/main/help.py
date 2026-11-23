
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTextBrowser
)


class HelpMixin:

  def open_help(self):

    if self.help_dialog is None:

      self.help_dialog = QDialog(self)
      self.help_dialog.setWindowIcon(self.windowIcon())
      self.help_dialog.setWindowTitle("Справка — Geometry Playground")
      self.help_dialog.resize(850, 700)
      self.help_dialog.setModal(False)

      layout = QVBoxLayout(self.help_dialog)

      self.help_browser = QTextBrowser()
      self.help_browser.setOpenExternalLinks(True)

      layout.addWidget(self.help_browser)

      help_path = Path(__file__).resolve().parent.parent / "help.md"

      if help_path.exists():

        markdown = help_path.read_text(encoding="utf-8")
        self.help_browser.setMarkdown(markdown)

      else:

        self.help_browser.setMarkdown(
            "# Справка\n\n"
            "Файл `help.md` не найден.\n\n"
            f"Ожидаемый путь: `{help_path}`"
        )

    self.help_dialog.show()
    self.help_dialog.raise_()
    self.help_dialog.activateWindow()

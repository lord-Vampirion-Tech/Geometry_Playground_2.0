import sys

from PySide6.QtWidgets import QApplication

from app.project_manager_window import ProjectManagerWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Geometry Playground")
    app.setOrganizationName("ZifTech")

    window = ProjectManagerWindow()
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

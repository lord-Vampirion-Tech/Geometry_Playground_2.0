import sys

from PySide6.QtWidgets import QApplication

from app.crash_handler import (
    install_crash_handler,
    report_exception,
    set_crash_context
)


def main():
    install_crash_handler()

    try:
        set_crash_context("Создание QApplication")
        app = QApplication(sys.argv)
        app.setApplicationName("Geometry Playground")
        app.setOrganizationName("ZifTech")

        set_crash_context("Импорт ProjectManagerWindow")
        from app.project_manager_window import ProjectManagerWindow

        set_crash_context("Создание окна менеджера проектов")
        window = ProjectManagerWindow()

        set_crash_context("Отображение окна менеджера проектов")
        window.show()

        set_crash_context("Работа главного цикла Qt")
        return app.exec()

    except Exception:
        report_exception("Запуск приложения", sys.exc_info())
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

import os
import subprocess
import sys
import winreg

from PySide6.QtWidgets import QApplication

from app.crash_handler import (
    install_crash_handler,
    report_exception,
    set_crash_context
)


_GPU_RESTART_MARKER = "GEOMETRY_PLAYGROUND_GPU_PREFERENCE_SET"


def _restart_with_high_performance_gpu():
    if not getattr(sys, "frozen", False):
        return False

    if os.environ.get(_GPU_RESTART_MARKER) == "1":
        return False

    registry_path = r"Software\\Microsoft\\DirectX\\UserGpuPreferences"
    executable = os.path.abspath(sys.executable)
    preference = "GpuPreference=2;"

    try:
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, registry_path) as key:
            try:
                current, _ = winreg.QueryValueEx(key, executable)
            except FileNotFoundError:
                current = None

            if current == preference:
                return False

            winreg.SetValueEx(key, executable, 0, winreg.REG_SZ, preference)

        env = os.environ.copy()
        env[_GPU_RESTART_MARKER] = "1"
        subprocess.Popen(
            [executable, *sys.argv[1:]],
            cwd=os.getcwd(),
            env=env
        )
        return True

    except OSError:
        return False


def main():
    if _restart_with_high_performance_gpu():
        return 0

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

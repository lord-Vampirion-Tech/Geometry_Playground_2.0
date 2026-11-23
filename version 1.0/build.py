
import sys
import shutil
import subprocess

from pathlib import Path


ROOT = Path(__file__).resolve().parent

ENTRY_POINT = ROOT / "run.py"
ICON = ROOT / "assets" / "app.ico"
HELP = ROOT / "help.md"

BUILD_DIR = ROOT / ".build"
DIST_DIR = BUILD_DIR / "dist"
WORK_DIR = BUILD_DIR / "work"

OUTPUT_EXE = ROOT / "Geometry Playground.exe"
BUILT_EXE = DIST_DIR / "Geometry Playground.exe"


def build():

    print("=" * 50)
    print("Geometry Playground — сборка")
    print("=" * 50)

    if not ENTRY_POINT.exists():
        print("ОШИБКА: run.py не найден.")
        return False

    if not ICON.exists():
        print("ОШИБКА: assets/app.ico не найден.")
        return False

    if not HELP.exists():
        print("ОШИБКА: help.md не найден.")
        return False

    if not BUILD_DIR.exists():
        BUILD_DIR.mkdir(parents=True)

    else:
        shutil.rmtree(BUILD_DIR)
        BUILD_DIR.mkdir(parents=True)

    command = [
        sys.executable,
        "-m",
        "PyInstaller",

        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",

        "--name",
        "Geometry Playground",

        "--icon",
        str(ICON),

        "--add-data",
        f"{HELP};.",

        "--add-data",
        f"{ICON};assets",

        "--collect-all",
        "pyvista",

        "--collect-all",
        "pyvistaqt",

        "--collect-all",
        "vtkmodules",

        "--collect-all",
        "pyqtgraph",

        str(ENTRY_POINT)
    ]

    command.extend([
        "--distpath", str(DIST_DIR),
        "--workpath", str(WORK_DIR),
        "--specpath", str(BUILD_DIR)
    ])

    print("\nНачинаем сборку...\n")

    result = subprocess.run(
        command,
        cwd=ROOT
    )

    if result.returncode != 0:
        print("\nОШИБКА: сборка не удалась.")
        print("Старый EXE сохранён.")
        return False

    if not BUILT_EXE.exists():
        print("\nОШИБКА: готовый EXE не найден.")
        return False

    temporary_exe = ROOT / "Geometry Playground.new.exe"

    shutil.copy2(BUILT_EXE, temporary_exe)
    temporary_exe.replace(OUTPUT_EXE)

    print("\n" + "=" * 50)
    print("СБОРКА УСПЕШНО ЗАВЕРШЕНА")
    print("=" * 50)
    print(f"\nФайл: {OUTPUT_EXE}")

    return True


if __name__ == "__main__":

    if not build():
        input("\nНажмите Enter для выхода...")
        sys.exit(1)

    input("\nНажмите Enter для выхода...")

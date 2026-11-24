
import sys
import winreg
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
APP = ROOT / "run.py"
PYTHON = Path(sys.executable).resolve()

if sys.platform != "win32":
  raise RuntimeError("Этот лаунчер предназначен для Windows.")

if not APP.exists():
  raise FileNotFoundError(f"Не найден файл: {APP}")

registry_path = r"Software\Microsoft\DirectX\UserGpuPreferences"

with winreg.CreateKey(
    winreg.HKEY_CURRENT_USER,
    registry_path
) as key:
  winreg.SetValueEx(
      key,
      str(PYTHON),
      0,
      winreg.REG_SZ,
      "GpuPreference=2;"
  )

print(f"Python: {PYTHON}")
print("Предпочтительная видеокарта: высокая производительность")
print("Запуск Geometry Playground...")



subprocess.Popen(
    [str(PYTHON), str(APP), *sys.argv[1:]],
    cwd=str(ROOT)
)

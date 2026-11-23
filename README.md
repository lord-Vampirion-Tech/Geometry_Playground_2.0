# Geometry Playground 2.0 — стартовый каркас

## Требования
- Windows 10/11
- Python 3.12

## Установка
```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Запуск
```powershell
python run.py
```

При первом запуске программа попросит выбрать папку, в которой будут храниться проекты.

## Структура
- `run.py` — точка входа.
- `app/settings.py` — настройки приложения (`settings.json` в системной папке конфигурации).
- `app/project_store.py` — создание, чтение и удаление проектов.
- `app/project_manager_window.py` — окно менеджера проектов.
- `app/project_window.py` — пустое окно открытого проекта.

Проекты хранятся в отдельных папках. В каждой папке находится `project.json`.

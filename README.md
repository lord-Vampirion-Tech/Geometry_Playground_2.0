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


## API геометрии

В 2D-проекте:

```python
square = New_SQUARE(x=0, y=0, width=16, height=16)
print(square.x)

square.draw()

def update(Time):
    square.setRot(Time * 30)
```

В 3D-проекте:

```python
cube = New_CUBE(x=0, y=0, z=0, width=16)
print(cube.x)

cube.draw()

def update(Time):
    cube.setRot(Time * 20, Time * 30, 0)
```

Создание объекта не отображает его автоматически. Для добавления на сцену вызовите `draw()`. После этого методы изменения геометрии обновляют отображение автоматически.

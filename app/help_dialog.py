from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton


class HelpDialog(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Справка — Geometry Playground')
        self.resize(760, 680)

        layout = QVBoxLayout(self)
        browser = QTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setMarkdown(self._markdown(mode))
        layout.addWidget(browser)

        close_button = QPushButton('Закрыть')
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)

    @staticmethod
    def _markdown(mode):
        common = '''
# Geometry Playground — справочник команд

## Общие правила

Код проекта выполняется как Python. Конструкторы фигур возвращают объект. Для отображения вызовите **draw()**.

Цвет всех фигур по умолчанию: **#42a5f5**. Цвет можно переопределить аргументом **color**.

## UI-параметры

### ui.slider(name, min=0, max=100, value=50, step=1, label=None)

Создаёт числовой ползунок и возвращает его начальное значение.

### ui.checkbox(name, value=False, label=None)

Создаёт флажок и возвращает начальное логическое значение.

### ui.input(name, value=0, type=float, min=None, max=None, step=None, decimals=6, label=None)

Создаёт числовое поле ввода. Поддерживает **int** и **float**.

### Группировка

- **ui.column(spacing=6, margins=0)** — вертикальная группа.
- **ui.row(spacing=8, margins=0)** — горизонтальная группа.
- **ui.grid(columns=2, spacing=8, row_spacing=None, margins=0)** — сетка с заполнением слева направо.

Группы можно вкладывать друг в друга.

## Анимация

Объявите **update(Time)**. Аргумент **Time** — время в секундах с начала выполнения.

```python
def update(Time):
    pass
```
'''
        if mode == '2D':
            commands = '''
## Геометрия 2D

### Point(x=0, y=0, color='#42a5f5', size=8)

Создаёт точку на плоскости.

### Line(x1=0, y1=0, x2=16, y2=0, color='#42a5f5', width=2)

Создаёт отрезок между двумя точками.

### Square(x=0, y=0, width=16, height=None, color='#42a5f5', angle=0)

Создаёт квадрат или прямоугольник. Если height не задан, используется width.

### Polygon(points, color='#42a5f5', width=2)

Создаёт замкнутый многоугольник по списку координат.

```python
triangle = Polygon([(0, 0), (16, 0), (8, 12)])
triangle.draw()
```

### Circle(x=0, y=0, radius=8, color='#42a5f5', width=2)

Создаёт окружность с заданным радиусом.

```python
point = Point(0, 0)
line = Line(-8, 0, 8, 0)
square = Square(width=16)
circle = Circle(x=12, y=0, radius=6)

for shape in (point, line, square, circle):
    shape.draw()
```
'''
        else:
            commands = '''
## Геометрия 3D

### Point(x=0, y=0, z=0, name=None, color='#42a5f5', opacity=1.0)

Создаёт 3D-точку. Необязательный name отображается рядом с точкой.

### Line(x1=0, y1=0, z1=0, x2=16, y2=0, z2=0, color='#42a5f5', width=2)

Создаёт отрезок в трёхмерном пространстве.

### Cube(x=0, y=0, z=0, width=16, height=None, depth=None, color='#42a5f5', opacity=1.0)

Создаёт куб или прямоугольный параллелепипед.

### BoundingCube(minx, miny, minz, maxx, maxy, maxz, color='#42a5f5', opacity=1.0)

Создаёт объём по минимальным и максимальным координатам.

### Sphere(x=0, y=0, z=0, radius=8, color='#42a5f5', opacity=1.0)

Создаёт сферу с заданным радиусом.

```python
point = Point(0, 0, 0, name='Center')
line = Line(0, 0, 0, 16, 8, 0)
cube = Cube(x=0, y=0, z=0, width=8)
bounds = BoundingCube(-8, -8, -8, 8, 8, 8)
sphere = Sphere(x=12, y=0, z=0, radius=4)

for shape in (point, line, cube, bounds, sphere):
    shape.draw()
```
'''
        shortcuts = '''
## Методы объектов

| Метод | Назначение |
|---|---|
| draw() | Отобразить объект; возвращает сам объект |
| setColor(color) | Изменить цвет |
| setPos(x, y) / setPos(x, y, z) | Изменить положение |
| setRot(...) | Изменить поворот, если поддерживается фигурой |
| setSize(...) | Изменить размеры, если поддерживается фигурой |
| setRadius(radius) | Изменить радиус Circle или Sphere |
| setPoints(...) | Изменить точки Line или Polygon |
| setOpacity(opacity) | Изменить прозрачность 3D-объекта от 0 до 1 |

## Совместимость

Старые конструкторы New_SQUARE(), New_CUBE(), New_BOUNDS() и New_POINT() пока поддерживаются для существующих проектов. Для нового кода используйте конструкторы классов выше.

## Сочетания клавиш редактора

| Сочетание | Действие |
|---|---|
| Ctrl + S | Сохранить проект |
| Ctrl + / | Закомментировать или раскомментировать строки |
| Tab | Добавить отступ |
| Shift + Tab | Уменьшить отступ |
'''
        return common + commands + shortcuts

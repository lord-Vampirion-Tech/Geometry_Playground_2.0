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

Можно использовать стандартные модули Python, например `math` и `random`, а также циклы, функции, списки и словари.

Цвет фигур по умолчанию: **#42a5f5**. Цвет можно переопределить аргументом **color**.

## UI-параметры

### ui.slider(name, min=0, max=100, value=50, step=1, label=None)

Создаёт числовой ползунок и возвращает его текущее значение.

```python
speed = ui.slider("speed", min=0, max=20, value=5, step=0.5)
```

### ui.checkbox(name, value=False, label=None)

Создаёт флажок и возвращает логическое значение `True` или `False`.

```python
enabled = ui.checkbox("enabled", value=True, label="Включено")
```

### ui.input(name, value=0, type=float, min=None, max=None, step=None, decimals=6, label=None)

Создаёт числовое поле ввода. Поддерживаются типы **int** и **float**. Если границы не заданы, поле не ограничивается ими.

```python
count = ui.input("count", value=10, type=int, min=1, max=100)
mass = ui.input("mass", value=2.5, type=float, min=0, step=0.1)
```

### ui.slider2d(name, x_min=-1, x_max=1, x_value=0, x_step=0.1, y_min=-1, y_max=1, y_value=0, y_step=0.1, label=None)

Создаёт двумерный ползунок. Перетаскивайте точку внутри области, чтобы одновременно менять координаты X и Y. Для каждой оси задаются собственные границы, начальное значение и шаг.

Возвращает объект со значениями **.val[0]** (X) и **.val[1]** (Y). Значения также можно менять программно через **.x_value**, **.y_value** или **.set_values(x, y)**.

```python
target = ui.slider2d(
    "target",
    x_min=-16, x_max=16, x_value=0, x_step=0.1,
    y_min=-16, y_max=16, y_value=8, y_step=0.1,
    label="Цель"
)

def update(Time):
    x, y = target.val
```

### ui.button(name, label=None, on_press=None, on_release=None, key=None)

Создаёт функциональную кнопку. **on_press** вызывается один раз при нажатии, **on_release** — при отпускании. Обработчики — обычные функции без аргументов. Кнопку можно активировать мышью или назначенной клавишей через **key**. Функция `ui.button` не возвращает значение.

```python
def fire():
    print("Нажали")

def stop_fire():
    print("Отпустили")

ui.button(
    "fire",
    label="Огонь",
    on_press=fire,
    on_release=stop_fire,
    key="SPACE"
)
```

### ui.hold_button(name, label=None, key=None)

Создаёт кнопку удержания и возвращает начальное значение **False**. Пока кнопка удерживается мышью или назначенной клавишей, переменная становится **True**. После отпускания всех источников удержания значение возвращается к **False**. Проверяйте его внутри `update(Time)`.

```python
boost = ui.hold_button("boost", label="Ускорение", key="SHIFT")

def update(Time):
    if boost:
        pass  # Действие во время удержания
```

### Группировка UI

Группы создаются как контекстные менеджеры с помощью **with**. Внутри группы размещайте обычные UI-элементы. Группы можно вкладывать друг в друга.

- **ui.row(spacing=8, margins=0)** — горизонтальная группа.
- **ui.column(spacing=6, margins=0)** — вертикальная группа.
- **ui.grid(columns=2, spacing=8, row_spacing=None, margins=0)** — сетка с заполнением слева направо.

```python
with ui.row():
    ui.button("left", label="Влево")
    ui.button("right", label="Вправо")

with ui.column():
    speed = ui.slider("speed", min=0, max=20, value=5)
    enabled = ui.checkbox("enabled", label="Активно")

with ui.grid(columns=2):
    x = ui.input("x", value=0.0)
    y = ui.input("y", value=0.0)
```

## Анимация и время

Объявите функцию **update(Time)**. Она вызывается при обновлении симуляции в режиме реального времени. **Time** — общее время в секундах с начала выполнения, а не длительность одного кадра.

Для расчёта движения используйте разницу между текущим и предыдущим временем:

```python
previous_time = 0

def update(Time):
    global previous_time

    dt = Time - previous_time
    previous_time = Time

    # Используйте dt для расчёта движения
```

В режиме одного выполнения код запускается один раз. Для непрерывной анимации включите режим **«Выполнять в реальном времени»**.

## Пример: случайные объекты

```python
import random

balls = []

for i in range(10):
    x = random.uniform(-10, 10)
    y = random.uniform(0, 15)
    radius = random.uniform(0.5, 2)

    ball = Circle(x=x, y=y, radius=radius)
    ball.draw()
    balls.append(ball)
```
'''
        if mode == '2D':
            commands = '''
## Геометрия 2D

### Point(x=0, y=0, color='#42a5f5', size=8)

Создаёт точку на плоскости.

### Line(x1=0, y1=0, x2=16, y2=0, color='#42a5f5', width=2)

Создаёт отрезок между двумя точками. Координаты передаются четырьмя отдельными аргументами.

### Square(x=0, y=0, width=16, height=None, color='#42a5f5', angle=0)

Создаёт квадрат или прямоугольник. Если **height** не задан, используется **width**.

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

Создаёт 3D-точку. Необязательный **name** отображается рядом с точкой.

### Line(x1=0, y1=0, z1=0, x2=16, y2=0, z2=0, color='#42a5f5', width=2)

Создаёт отрезок в трёхмерном пространстве.

### Cube(x=0, y=0, z=0, width=16, height=None, depth=None, color='#42a5f5', opacity=1.0)

Создаёт куб или прямоугольный параллелепипед.

### BoundingCube(minx, miny, minz, maxx, maxy, maxz, color='#42a5f5', opacity=1.0)

Создаёт объём по минимальным и максимальным координатам.

### Sphere(x=0, y=0, z=0, radius=8, color='#42a5f5', opacity=1.0)

Создаёт сферу с заданным радиусом.

```python
point = Point(0, 0, 0, name="Center")
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

## Сочетания клавиш редактора

| Сочетание | Действие |
|---|---|
| Ctrl + S | Сохранить проект |
| Ctrl + / | Закомментировать или раскомментировать строки |
| Tab | Добавить отступ |
| Shift + Tab | Уменьшить отступ |
'''
        return common + commands + shortcuts

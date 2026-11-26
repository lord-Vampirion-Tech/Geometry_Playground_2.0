from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QTextBrowser,
)


class HelpTextBrowser(QTextBrowser):
    zoom_requested = Signal(int)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            if delta:
                self.zoom_requested.emit(1 if delta > 0 else -1)
                event.accept()
                return
        super().wheelEvent(event)


class HelpDialog(QDialog):
    def __init__(self, mode, parent=None):
        super().__init__(None)
        self.setWindowFlag(Qt.WindowType.Window, True)
        self.mode = mode
        self._zoom_level = 0
        self._browsers = []

        self.setWindowTitle("Справка — Geometry Playground 2.0")
        self.resize(980, 780)
        self.setMinimumSize(720, 560)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        heading = QLabel("Справочник API")
        heading.setObjectName("helpHeading")
        subtitle = QLabel(
            f"Режим проекта: {mode} · Сигнатуры и примеры соответствуют текущей реализации"
        )
        subtitle.setObjectName("helpSubtitle")

        layout.addWidget(heading)
        layout.addWidget(subtitle)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs, 1)

        self._add_tab("Начало", self._intro_markdown())
        self._add_tab("UI", self._ui_markdown())
        self._add_tab("Геометрия", self._geometry_markdown(mode))
        self._add_tab("Методы объектов", self._methods_markdown(mode))

        self.setStyleSheet("""
            QLabel#helpHeading {
                font-size: 20px;
                font-weight: 700;
            }
            QLabel#helpSubtitle {
                color: #aab2c0;
                padding-bottom: 3px;
            }
            QTabWidget::pane {
                border: 1px solid #454b56;
                border-radius: 6px;
                top: -1px;
                background: #20232b;
            }
            QTabBar::tab {
                color: #e8eaf0;
                background: #2b303b;
                border: 1px solid #454b56;
                border-bottom: none;
                border-radius: 5px 5px 0 0;
                padding: 8px 14px;
                margin-right: 3px;
            }
            QTabBar::tab:hover {
                background: #343b49;
                border-color: #454b56;
            }
            QTabBar::tab:selected {
                background: #20232b;
                border-color: #454b56;
                color: #ffffff;
            }
        """)

    def _add_tab(self, title, markdown):
        browser = HelpTextBrowser()
        browser.setOpenExternalLinks(True)
        browser.setReadOnly(True)
        browser.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)

        fixed_font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
        fixed_font.setPointSize(10)
        browser.document().setDefaultFont(self.font())
        browser.zoom_requested.connect(self._change_zoom)
        self._browsers.append(browser)
        browser.document().setDefaultStyleSheet(f"""
            body {{
                color: #e8eaf0;
                font-size: 100%;
                line-height: 1.35;
            }}
            h1, h2, h3 {{
                color: #e8eaf0;
                margin-top: 16px;
                margin-bottom: 7px;
            }}
            h1 {{ font-size: 1.8em; }}
            h2 {{
                font-size: 1.4em;
                border-bottom: 1px solid #454b56;
                padding-bottom: 4px;
            }}
            h3 {{ font-size: 1.15em; }}
            p, li {{ margin-top: 4px; margin-bottom: 4px; }}
            code {{
                font-family: "{fixed_font.family()}";
                background-color: #20232b;
                color: #e8eaf0;
                padding: 2px 4px;
            }}
            pre {{
                font-family: "{fixed_font.family()}";
                font-size: 90%;
                background-color: #20232b;
                color: #e8eaf0;
                border: 1px solid #454b56;
                border-radius: 6px;
                padding: 10px;
                margin-top: 6px;
                margin-bottom: 12px;
                white-space: pre-wrap;
            }}
            pre code {{
                background: transparent;
                padding: 0;
            }}
            table {{
                border-collapse: collapse;
            }}
            th, td {{
                border: 1px solid #454b56;
                padding: 5px 8px;
            }}
            blockquote {{
                border-left: 3px solid #42a5f5;
                margin-left: 5px;
                padding-left: 10px;
                color: palette(mid);
            }}
        """)
        browser.setMarkdown(markdown)
        self.tabs.addTab(browser, title)

    def _change_zoom(self, delta):
        self._zoom_level = max(-5, min(10, self._zoom_level + delta))
        font = self.font()
        base_size = font.pointSize() or 10
        font.setPointSize(max(7, min(24, base_size + self._zoom_level)))
        for browser in self._browsers:
            browser.setFont(font)
            browser.document().setDefaultFont(font)

    @staticmethod
    def _intro_markdown():
        return r"""
# Как пользоваться справочником

В редакторе выполняется обычный Python-код. Классы геометрии текущего режима доступны напрямую: например, `Circle(...)` или `Cube(...)`. Для появления фигуры в рабочей области вызовите `draw()`.

## Общие правила

- Координаты и размеры задаются в условных единицах сцены.
- Цвет по умолчанию — `#42a5f5`. Можно передать цвет в формате HEX или другой формат, поддерживаемый используемым движком.
- Для непрерывного обновления объявите функцию `update(Time)` и включите режим **«Выполнять в реальном времени»**.
- Параметры UI создаются при выполнении программы. В режиме реального времени они отображаются в панели **«UI элементы»**.
- Вызов конструктора создаёт объект, но сам по себе не отображает его. Нужен вызов `draw()`.

## Анимация: update(Time)

**Как вызвать**

```python
def update(Time):
    # Time — время с начала текущего запуска, в секундах
    pass
```

**Параметры**

- `Time` — текущее время симуляции в секундах. Это абсолютное время с начала запуска, а не длительность кадра.

**Пример: движение по окружности**

```python
ball = Circle(radius=2)
ball.draw()

def update(Time):
    ball.setPos(
        math.cos(Time) * 5,
        math.sin(Time) * 5
    )
```

Если нужна скорость, независимая от частоты кадров, вычисляйте `dt` как разницу между текущим и предыдущим значением `Time`.

```python
previous_time = 0.0
position = 0.0
speed = 3.0

def update(Time):
    global previous_time, position

    dt = Time - previous_time
    previous_time = Time
    position += speed * dt
```

## Однократный запуск и реальное время

- **Однократный запуск:** код выполняется один раз. Функция `update(0)`, если она объявлена, вызывается при старте.
- **Реальное время:** после выполнения кода `update(Time)` вызывается повторно по мере обновления сцены.
- При изменении значения UI-параметра `update(Time)` вызывается сразу с текущим временем.
- Кнопки могут вызывать обработчики при нажатии и отпускании.

## Сочетания клавиш редактора

| Сочетание | Действие |
|---|---|
| `Ctrl + S` | Сохранить проект |
| `Ctrl + /` | Закомментировать или раскомментировать выбранные строки |
| `Tab` | Добавить отступ |
| `Shift + Tab` | Уменьшить отступ |

## Доступные модули

Модуль `math` подключён автоматически. Можно сразу использовать `math.sin()`, `math.cos()`, `math.pi` и остальные его функции без `import math`.

```python
angle = math.pi / 4
x = math.cos(angle)
y = math.sin(angle)
```

Другие стандартные модули Python импортируются обычным способом. Доступность сторонних пакетов зависит от окружения приложения.
"""

    @staticmethod
    def _ui_markdown():
        return r"""
# UI API

Все элементы создаются через объект `ui`. Первый аргумент — уникальное имя переменной. Это имя также используется для передачи нового значения в пространство имён кода проекта.

## ui.slider()

**Как вызвать**

```python
speed = ui.slider(
    "speed",
    min=0, max=20,
    value=5, step=0.5,
    label="Скорость"
)
```

**Параметры**

- `name` — обязательное имя параметра. Должно быть корректным Python-идентификатором.
- `min` — минимальное значение, по умолчанию `0`.
- `max` — максимальное значение, по умолчанию `100`.
- `value` — начальное значение, по умолчанию `50`.
- `step` — шаг изменения, по умолчанию `1`. Должен быть больше нуля.
- `label` — подпись в интерфейсе. По умолчанию используется `name`.

**Возвращает:** начальное числовое значение ползунка.

## ui.slider2d()

**Как вызвать**

```python
target = ui.slider2d(
    "target",
    x_min=-16, x_max=16, x_value=0, x_step=0.1,
    y_min=-10, y_max=10, y_value=2, y_step=0.1,
    label="Цель"
)
```

**Параметры**

- `name` — обязательное уникальное имя.
- `x_min`, `x_max` — нижняя и верхняя границы оси X.
- `x_value` — начальное значение X.
- `x_step` — шаг X.
- `y_min`, `y_max` — нижняя и верхняя границы оси Y.
- `y_value` — начальное значение Y.
- `y_step` — шаг Y.
- `label` — подпись элемента; по умолчанию `name`.

Для обеих осей шаг должен быть положительным, а максимальное значение — больше минимального.

**Возвращает:** объект значения с атрибутами `.val`, `.x_value`, `.y_value` и методом `.set_values(x, y)`.

- `.val` — пара `(x, y)`.
- `.x_value` — текущее значение X; доступна запись.
- `.y_value` — текущее значение Y; доступна запись.
- `.set_values(x, y)` — установить обе координаты. Значения ограничиваются диапазонами и округляются к шагу.

**Пример**

```python
target = ui.slider2d(
    "target",
    x_min=-10, x_max=10, x_value=3,
    y_min=-10, y_max=10, y_value=5
)

marker = Point()
marker.draw()

def update(Time):
    x, y = target.val
    marker.setPos(x, y)
```

## ui.checkbox()

**Как вызвать**

```python
enabled = ui.checkbox(
    "enabled",
    value=True,
    label="Включено"
)
```

**Параметры**

- `name` — обязательное уникальное имя.
- `value` — начальное логическое значение, по умолчанию `False`.
- `label` — подпись; по умолчанию `name`.

**Возвращает:** `bool` — `True` или `False`.

## ui.input()

**Как вызвать**

```python
count = ui.input(
    "count",
    value=10,
    type=int,
    min=1, max=100,
    step=1,
    label="Количество"
)

mass = ui.input(
    "mass",
    value=2.5,
    type=float,
    min=0,
    max=10,
    step=0.1,
    decimals=2
)
```

**Параметры**

- `name` — обязательное уникальное имя.
- `value` — начальное числовое значение, по умолчанию `0`.
- `type` — тип значения: `int` или `float`. По умолчанию `float`.
- `min` — минимально допустимое значение; по умолчанию ограничение отсутствует.
- `max` — максимально допустимое значение; по умолчанию ограничение отсутствует.
- `step` — шаг кнопок изменения значения. По умолчанию `1` для `int` и `0.1` для `float`.
- `decimals` — число знаков после запятой для `float`, по умолчанию `6`.
- `label` — подпись; по умолчанию `name`.

**Возвращает:** начальное числовое значение типа `int` или `float`.

## ui.button()

**Как вызвать**

```python
def on_press():
    print("Нажато")

def on_release():
    print("Отпущено")

ui.button(
    "fire",
    label="Огонь",
    on_press=on_press,
    on_release=on_release,
    key="SPACE"
)
```

**Параметры**

- `name` — обязательное уникальное имя.
- `label` — текст кнопки; по умолчанию `name`.
- `on_press` — функция без аргументов, вызывается при нажатии.
- `on_release` — функция без аргументов, вызывается при отпускании.
- `key` — необязательная клавиша или сочетание клавиш. Используется формат Qt Portable Text, например `"SPACE"`, `"SHIFT"`, `"CTRL+K"`.

**Возвращает:** ничего.

После выполнения обработчика приложение повторно вызывает `update(Time)`, если такая функция определена.

## ui.hold_button()

**Как вызвать**

```python
boost = ui.hold_button(
    "boost",
    label="Ускорение",
    key="SHIFT"
)

def update(Time):
    if boost:
        pass  # Действие, пока кнопка удерживается
```

**Параметры**

- `name` — обязательное уникальное имя.
- `label` — текст кнопки; по умолчанию `name`.
- `key` — необязательная клавиша или сочетание клавиш.

**Возвращает:** начальное значение `False`. При удержании кнопки мышью или назначенной клавиши значение становится `True`; после отпускания всех источников удержания — `False`.

## Группы элементов

Группы используются через `with`. Вложенность поддерживается.

### ui.row()

**Вызов:** `with ui.row(spacing=8, margins=0):`

- `spacing` — расстояние между элементами, по умолчанию `8`.
- `margins` — внутренние отступы группы, по умолчанию `0`.

Размещает элементы горизонтально.

### ui.column()

**Вызов:** `with ui.column(spacing=6, margins=0):`

- `spacing` — расстояние между элементами, по умолчанию `6`.
- `margins` — внутренние отступы группы, по умолчанию `0`.

Размещает элементы вертикально.

### ui.grid()

**Вызов:** `with ui.grid(columns=2, spacing=8, row_spacing=None, margins=0):`

- `columns` — количество столбцов, по умолчанию `2`; должно быть целым числом больше нуля.
- `spacing` — горизонтальный шаг между элементами, по умолчанию `8`.
- `row_spacing` — вертикальный шаг; если не задан, используется `spacing`.
- `margins` — внутренние отступы группы, по умолчанию `0`.

Элементы добавляются слева направо, затем переходят на следующую строку.

**Пример вложенных групп**

```python
with ui.column(spacing=10):
    enabled = ui.checkbox("enabled", label="Активно")

    with ui.row():
        x = ui.input("x", value=0.0, label="X")
        y = ui.input("y", value=0.0, label="Y")

    with ui.grid(columns=2):
        ui.button("left", label="Влево")
        ui.button("right", label="Вправо")
```

## Важные особенности UI

- Чтобы элементы отображались в панели, включите **«Выполнять в реальном времени»**.
- При изменении ползунка, флажка или поля ввода новое значение записывается в переменную с именем `name`.
- Для реакции на изменения в реальном времени используйте `update(Time)`.
- Обработчики `on_press` и `on_release` должны быть функциями без обязательных аргументов.
"""

    @staticmethod
    def _geometry_markdown(mode):
        common_2d = r"""
# Геометрия 2D

## Point()

**Как вызвать**

```python
point = Point(x=2, y=4, color="#ff5252", size=10)
point.draw()
```

**Параметры**

- `x`, `y` — координаты точки, по умолчанию `0`.
- `color` — цвет точки, по умолчанию `"#42a5f5"`.
- `size` — размер точки, по умолчанию `8`.

**Возвращает:** объект `Point`.

## Line()

**Как вызвать**

```python
line = Line(x1=-5, y1=0, x2=5, y2=8, color="#00c853", line_width=3)
line.draw()
```

**Параметры**

- `x1`, `y1` — координаты начала отрезка, по умолчанию `(0, 0)`.
- `x2`, `y2` — координаты конца отрезка, по умолчанию `(16, 0)`.
- `color` — цвет линии, по умолчанию `"#42a5f5"`.
- `line_width` — толщина линии, по умолчанию `2`.

**Возвращает:** объект `Line`.

## Square()

Несмотря на название, класс создаёт как квадрат, так и прямоугольник.

**Как вызвать**

```python
square = Square(
    x=0, y=0,
    width=12, height=6,
    color="#42a5f5",
    angle=30,
    line_width=2
)
square.draw()
```

**Параметры**

- `x`, `y` — координаты центра фигуры, по умолчанию `0`.
- `width` — ширина, по умолчанию `16`.
- `height` — высота. Если не задана, равна `width`.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `angle` — угол поворота в градусах, по умолчанию `0`.
- `line_width` — толщина контура, по умолчанию `2`.

**Возвращает:** объект `Square`.

## Polygon()

**Как вызвать**

```python
triangle = Polygon(
    points=[(0, 0), (10, 0), (5, 8)],
    color="#ff9800",
    line_width=2
)
triangle.draw()
```

**Параметры**

- `points` — обязательный список или другой итерируемый объект координат вида `(x, y)`. Нужно минимум три точки.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `line_width` — толщина контура, по умолчанию `2`.

**Возвращает:** объект `Polygon`.

## Circle()

**Как вызвать**

```python
circle = Circle(
    x=0, y=0,
    radius=5,
    color="#42a5f5",
    line_width=2,
    segments=64
)
circle.draw()
```

**Параметры**

- `x`, `y` — координаты центра, по умолчанию `0`.
- `radius` — радиус, по умолчанию `8`.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `width` — толщина контура, по умолчанию `2`.
- `segments` — количество сегментов аппроксимации окружности, по умолчанию `64`; фактическое значение не может быть меньше `12`.

**Возвращает:** объект `Circle`.
"""

        common_3d = r"""
# Геометрия 3D

## Point()

**Как вызвать**

```python
point = Point(
    x=0, y=0, z=0,
    name="Центр",
    color="#ff5252",
    opacity=1.0
)
point.draw()
```

**Параметры**

- `x`, `y`, `z` — координаты точки, по умолчанию `0`.
- `name` — необязательная подпись рядом с точкой.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `opacity` — прозрачность от `0.0` до `1.0`, по умолчанию `1.0`.

**Возвращает:** объект `Point`.

## Line()

**Как вызвать**

```python
line = Line(
    x1=0, y1=0, z1=0,
    x2=8, y2=5, z2=3,
    color="#00c853",
    line_width=3
)
line.draw()
```

**Параметры**

- `x1`, `y1`, `z1` — координаты начала отрезка, по умолчанию `(0, 0, 0)`.
- `x2`, `y2`, `z2` — координаты конца отрезка, по умолчанию `(16, 0, 0)`.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `width` — толщина линии, по умолчанию `2`.

**Возвращает:** объект `Line`.

## Cube()

Создаёт куб или прямоугольный параллелепипед. Начальное положение задаётся центром фигуры.

**Как вызвать**

```python
cube = Cube(
    x=0, y=0, z=0,
    width=8, height=6, depth=10,
    color="#42a5f5",
    opacity=0.8
)
cube.draw()
```

**Параметры**

- `x`, `y`, `z` — координаты центра, по умолчанию `0`.
- `width` — размер по X, по умолчанию `16`.
- `height` — размер по Y. Если не задан, равен `width`.
- `depth` — размер по Z. Если не задан, равен `width`.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `opacity` — прозрачность от `0.0` до `1.0`, по умолчанию `1.0`.

**Возвращает:** объект `Cube`.

## BoundingCube()

Создаёт прямоугольный объём по минимальным и максимальным координатам. Это наследник `Cube`.

**Как вызвать**

```python
bounds = BoundingCube(
    minx=-5, miny=-3, minz=-2,
    maxx=5, maxy=3, maxz=2,
    color="#ff9800",
    opacity=0.25
)
bounds.draw()
```

**Параметры**

- `minx`, `miny`, `minz` — минимальные координаты объёма.
- `maxx`, `maxy`, `maxz` — максимальные координаты объёма.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `opacity` — прозрачность от `0.0` до `1.0`, по умолчанию `1.0`.

Минимальная координата каждой оси не должна превышать максимальную.

**Возвращает:** объект `BoundingCube`.

## Sphere()

**Как вызвать**

```python
sphere = Sphere(
    x=0, y=0, z=0,
    radius=5,
    color="#42a5f5",
    opacity=0.9,
    theta_resolution=32,
    phi_resolution=32
)
sphere.draw()
```

**Параметры**

- `x`, `y`, `z` — координаты центра, по умолчанию `0`.
- `radius` — радиус, по умолчанию `8`.
- `color` — цвет, по умолчанию `"#42a5f5"`.
- `opacity` — прозрачность от `0.0` до `1.0`, по умолчанию `1.0`.
- `theta_resolution` — разрешение сферы по долготе, по умолчанию `24`.
- `phi_resolution` — разрешение сферы по широте, по умолчанию `24`.

Увеличение разрешения делает поверхность визуально более гладкой, но увеличивает число полигонов.

**Возвращает:** объект `Sphere`.
"""
        return common_2d if mode == "2D" else common_3d

    @staticmethod
    def _methods_markdown(mode):
        if mode == "2D":
            return r"""
# Методы объектов 2D

У методов изменения геометрии нет необходимости повторно вызывать `draw()`: после первого отображения объект обновляет свою фигуру автоматически.

## Общие методы

### draw()

**Вызов:** `shape.draw()`

Добавляет объект в рабочую область. Возвращает сам объект, поэтому вызовы можно объединять. Если объект уже отображён, повторный вызов обновляет его отображение.

```python
circle = Circle(radius=4).draw()
```

### setColor(color)

**Параметры:** `color` — новый цвет.

Меняет цвет объекта и обновляет отображение.

```python
circle.setColor("#ff5252")
```

### setPos(x, y)

**Параметры:** `x`, `y` — новые координаты.

Перемещает объект. Поддерживается классами `Point`, `Square` и `Circle`.

```python
circle.setPos(5, 3)
```

## Методы отдельных фигур

### Point

- `setSize(size)` — изменить размер точки.

```python
point.setSize(12)
```

### Line

- `setPoints(x1, y1, x2, y2)` — задать новые координаты начала и конца.
- `setLineWidth(line_width)` — изменить толщину линии.

```python
line.setPoints(-5, 0, 5, 8)
line.setLineWidth(4)
```

### Square

- `setRot(angle, pivot_x=None, pivot_y=None)` — задать угол поворота в градусах. Параметры `pivot_x` и `pivot_y` присутствуют в сигнатуре, но текущая реализация их не использует.
- `setSize(width, height=None)` — изменить размеры. Если `height` не задана, используется `width`.
- `getPoint(name)` — получить координаты вершины `A`, `B`, `C` или `D`.
- `square[name]` — сокращённый способ получить координаты вершины.

```python
square.setRot(45)
square.setSize(10, 6)

point_a = square.getPoint("A")
point_b = square["B"]
```

### Polygon

- `setPoints(points)` — заменить список вершин. Нужно минимум три точки вида `(x, y)`.

```python
triangle.setPoints([(0, 0), (12, 0), (6, 10)])
```

### Circle

- `setRadius(radius)` — изменить радиус.

```python
circle.setRadius(7)
```

## Получение координат

### get_vertices()

Возвращает список координат вершин фигуры. У `Point` это одна пара координат, у `Line` — две, у `Polygon` — все заданные вершины. У `Square` и `Circle` возвращаются вычисленные вершины контура.

```python
vertices = square.get_vertices()
print(vertices)
```
"""
        return r"""
# Методы объектов 3D

После первого вызова `draw()` методы изменения объекта автоматически обновляют его отображение.

## Общие методы

### draw()

**Вызов:** `shape.draw()`

Добавляет объект в рабочую область и возвращает сам объект. Повторный вызов обновляет уже отображённый объект.

```python
cube = Cube(width=5).draw()
```

### setColor(color)

**Параметры:** `color` — новый цвет.

Изменяет цвет объекта.

```python
cube.setColor("#ff5252")
```

### setPos(x, y, z)

**Параметры:** `x`, `y`, `z` — новые координаты.

Перемещает объект. Поддерживается классами `Point`, `Cube`, `BoundingCube` и `Sphere`. Для перемещения 3D-линии используйте `setPoints(...)`.

```python
cube.setPos(3, 2, -1)
```

### setOpacity(opacity)

**Параметры:** `opacity` — прозрачность от `0.0` (прозрачный) до `1.0` (непрозрачный).

Изменяет прозрачность объекта.

```python
cube.setOpacity(0.35)
```

## Методы отдельных фигур

### Line

- `setPoints(x1, y1, z1, x2, y2, z2)` — изменить координаты обоих концов.
- `setLineWidth(line_width)` — изменить толщину линии.

```python
line.setPoints(0, 0, 0, 10, 5, 2)
line.setLineWidth(4)
```

### Cube

- `setRot(x=0, y=0, z=0)` — задать поворот вокруг осей X, Y и Z в градусах.
- `setSize(width, height=None, depth=None)` — изменить размеры. Неуказанные `height` и `depth` принимают значение `width`.
- `get_vertices()` — получить словарь координат вершин A–H.
- `getPoint(name)` — получить координаты вершины по имени A–H.
- `cube[name]` — сокращённый способ получить координаты вершины.
- `movePoint(name, x, y, z)` — переместить выбранную вершину в указанные мировые координаты.

```python
cube.setRot(x=30, y=45, z=0)
cube.setSize(8, 6, 10)

vertex_a = cube.getPoint("A")
vertex_b = cube["B"]

cube.movePoint("A", -5, -5, -5)
```

### BoundingCube

Наследует методы `Cube` и дополнительно предоставляет границы объёма.

- `setBounds(minx, miny, minz, maxx, maxy, maxz)` — изменить все шесть границ.
- `minx`, `miny`, `minz` — свойства минимальных координат; доступны для чтения и записи.
- `maxx`, `maxy`, `maxz` — свойства максимальных координат; доступны для чтения и записи.

Если новая минимальная граница превышает максимальную, значение не применяется.

```python
bounds.setBounds(-8, -4, -3, 8, 4, 3)
bounds.maxz = 5
print(bounds.minx, bounds.maxz)
```

### Sphere

- `setRadius(radius)` — изменить радиус.

```python
sphere.setRadius(10)
```

## Техническое замечание

Методы `to_polydata()`, `update_draw()` и внутренние методы преобразования вершин относятся к реализации геометрии и обычно не нужны в коде проекта. Для управления объектами используйте публичные методы, перечисленные выше.
"""

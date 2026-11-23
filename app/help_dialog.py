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

Код проекта выполняется как Python. Создавайте объекты функциями ниже и сохраняйте результат в переменную.

## UI-параметры

### ui.slider(name, min=0, max=100, value=50, step=1, label=None)

Создаёт числовой ползунок и возвращает его начальное значение.

| Аргумент | Назначение |
|---|---|
| name | Имя параметра — корректный Python-идентификатор |
| min / max | Минимальное и максимальное значение |
| value | Начальное значение |
| step | Шаг изменения, больше нуля |
| label | Отображаемая подпись |

### ui.checkbox(name, value=False, label=None)

Создаёт флажок и возвращает начальное логическое значение.

## Анимация

Объявите функцию update(Time). Аргумент Time — время в секундах с начала выполнения. При включённом режиме реального времени функция вызывается каждый кадр.

```python
def update(Time):
    pass
```
'''
        if mode == '2D':
            commands = '''
## Команды 2D

### New_SQUARE(x=0, y=0, width=16, height=16)

Создаёт квадрат или прямоугольник в 2D-сцене. Возвращает объект.

```python
square = New_SQUARE(x=0, y=0, width=16, height=16)
square.draw()
```
'''
        else:
            commands = '''
## Команды 3D

### New_CUBE(x=0, y=0, z=0, width=16)

Создаёт куб в 3D-сцене. Возвращает объект.

```python
cube = New_CUBE(x=0, y=0, z=0, width=16)
cube.draw()
cube.setRot(Time * 20, Time * 30, 0)
```

### New_BOUNDS(minx, miny, minz, maxx, maxy, maxz)

Создаёт ограничивающий объём по минимальным и максимальным координатам. Возвращает объект. Минимальные координаты не должны превышать максимальные.

```python
bounds = New_BOUNDS(minx=-8, miny=-8, minz=-8, maxx=8, maxy=8, maxz=8)
bounds.draw()
```
'''
        shortcuts = '''
## Методы объектов

### 2D-объект Square

| Метод | Назначение |
|---|---|
| draw() | Отобразить объект; возвращает сам объект |
| setPos(x, y) | Изменить положение |
| setRot(angle, pivot_x=None, pivot_y=None) | Задать угол поворота в градусах |
| setSize(width, height=None) | Изменить размеры |
| setColor(color) | Изменить цвет |
| getPoint(name) | Получить координаты вершины A–D |
| object['A'] | Получить координаты вершины по имени |

### 3D-объекты Cube и BoundingCube

| Метод | Назначение |
|---|---|
| draw() | Отобразить объект; возвращает сам объект |
| setPos(x, y, z) | Изменить положение |
| setRot(x=0, y=0, z=0) | Задать поворот вокруг осей X, Y и Z в градусах |
| setSize(width, height=None, depth=None) | Изменить размеры |
| setColor(color) | Изменить цвет |
| setOpacity(opacity) | Задать прозрачность от 0 до 1 |
| getPoint(name) | Получить координаты вершины A–H |
| movePoint(name, x, y, z) | Переместить вершину |
| object['A'] | Получить координаты вершины по имени |

Для вершины используйте буквы A–D у 2D-объекта и A–H у 3D-куба.
  
## Сочетания клавиш редактора

| Сочетание | Действие |
|---|---|
| Ctrl + S | Сохранить проект |
| Ctrl + / | Закомментировать или раскомментировать текущую строку / выделенные строки |
| Tab | Добавить отступ выделенным строкам или вставить четыре пробела |
| Shift + Tab | Уменьшить отступ выделенных строк |
| (, {, [, ", ' | Обрамить выделенный текст парными символами |
'''
        return common + commands + shortcuts

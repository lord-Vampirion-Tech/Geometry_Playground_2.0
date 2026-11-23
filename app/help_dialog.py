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

| Метод | Назначение |
|---|---|
| draw() | Отобразить объект в сцене; возвращает сам объект |
| setPos(x, y, z) | Изменить положение |
| setRot(x=0, y=0, z=0) | Задать поворот куба вокруг осей X, Y и Z в градусах |
| setSize(width, height=None, depth=None) | Изменить размеры куба |
| setColor(color) | Изменить цвет |
| setOpacity(opacity) | Изменить прозрачность от 0 до 1 |
| getPoint(name) | Получить координаты вершины |
| movePoint(name, x, y, z) | Переместить вершину куба |
| object['A'] | Получить координаты вершины по имени |

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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QCheckBox,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QPushButton,
)
from .slider2d import Slider2DValue, Slider2DCanvas


class UIElements:
    def __init__(self, on_change, add_widget, invoke_callback, register_key):
        self._on_change = on_change
        self._add_widget = add_widget
        self._invoke_callback = invoke_callback
        self._register_key = register_key

    def slider(self, name, minimum, maximum, value, step, label):
        count = round((maximum - minimum) / step)
        maximum_value = minimum + count * step
        value = max(minimum, min(maximum_value, value))
        index = round((value - minimum) / step)
        initial_value = minimum + index * step

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)

        title = QLabel(label)
        value_label = QLabel(f"{initial_value:g}")

        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(value_label)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setRange(0, count)
        slider.setValue(index)

        layout.addLayout(header)
        layout.addWidget(slider)
        self._add_widget(container)

        def on_value_changed(current_index):
            current_value = minimum + current_index * step
            value_label.setText(f"{current_value:g}")
            self._on_change(name, current_value)

        slider.valueChanged.connect(on_value_changed)
        return initial_value


    def slider2d(
        self,
        name,
        x_min, x_max, x_value, x_step,
        y_min, y_max, y_value, y_step,
        label,
    ):
        model = Slider2DValue(
            x_min, x_max, x_value, x_step,
            y_min, y_max, y_value, y_step,
        )

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)

        title = QLabel(label)
        value_label = QLabel(
            f"X: {model.val[0]:g}    Y: {model.val[1]:g}"
        )
        header = QHBoxLayout()
        header.addWidget(title)
        header.addStretch()
        header.addWidget(value_label)

        def on_value_changed(current):
            value_label.setText(
                f"X: {current.val[0]:g}    Y: {current.val[1]:g}"
            )
            canvas.update()
            self._on_change(name, current)

        canvas = Slider2DCanvas(model, on_value_changed)
        model.set_on_change(on_value_changed)
        layout.addLayout(header)
        layout.addWidget(canvas)
        self._add_widget(container)
        return model

    def checkbox(self, name, value, label):
        checkbox = QCheckBox(label)
        checkbox.setChecked(value)
        self._add_widget(checkbox)
        checkbox.toggled.connect(
            lambda checked: self._on_change(name, checked)
        )
        return value


    def button(self, name, label, on_press, on_release, key):
        button = QPushButton(label)
        self._add_widget(button)

        if on_press is not None:
            button.pressed.connect(
                lambda: self._invoke_callback(on_press, name, "press")
            )
        if on_release is not None:
            button.released.connect(
                lambda: self._invoke_callback(on_release, name, "release")
            )

        if key is not None:
            self._register_key(
                key,
                (lambda: self._invoke_callback(on_press, name, "press")) if on_press else None,
                (lambda: self._invoke_callback(on_release, name, "release")) if on_release else None,
            )

    def hold_button(self, name, label, key):
        button = QPushButton(label)
        self._add_widget(button)
        active_sources = set()

        def set_source(source, active):
            if active:
                active_sources.add(source)
            else:
                active_sources.discard(source)
            self._on_change(name, bool(active_sources))

        button.pressed.connect(lambda: set_source("mouse", True))
        button.released.connect(lambda: set_source("mouse", False))

        if key is not None:
            self._register_key(
                key,
                lambda: set_source("key", True),
                lambda: set_source("key", False),
            )

    def input(
        self,
        name,
        value,
        value_type,
        minimum,
        maximum,
        step,
        decimals,
        label,
    ):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 4)

        title = QLabel(label)
        layout.addWidget(title)
        layout.addStretch()

        if value_type is int:
            field = QSpinBox()
            field.setRange(
                -2147483648 if minimum is None else int(minimum),
                2147483647 if maximum is None else int(maximum),
            )
            field.setSingleStep(int(step))
            field.setValue(int(value))
        else:
            field = QDoubleSpinBox()
            field.setRange(
                -1e100 if minimum is None else minimum,
                1e100 if maximum is None else maximum,
            )
            field.setDecimals(decimals)
            field.setSingleStep(step)
            field.setValue(value)

        layout.addWidget(field)
        self._add_widget(container)
        field.valueChanged.connect(
            lambda current: self._on_change(name, current)
        )
        return field.value()


class UIElementFactory:
    def __init__(self, on_change, add_widget, invoke_callback, register_key):
        self.elements = UIElements(on_change, add_widget, invoke_callback, register_key)

    def slider(self, *args, **kwargs):
        return self.elements.slider(*args, **kwargs)

    def checkbox(self, *args, **kwargs):
        return self.elements.checkbox(*args, **kwargs)

    def slider2d(self, *args, **kwargs):
        return self.elements.slider2d(*args, **kwargs)

    def input(self, *args, **kwargs):
        return self.elements.input(*args, **kwargs)

    def button(self, *args, **kwargs):
        return self.elements.button(*args, **kwargs)

    def hold_button(self, *args, **kwargs):
        return self.elements.hold_button(*args, **kwargs)

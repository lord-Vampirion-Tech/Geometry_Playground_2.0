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
)


class UIElements:
    def __init__(self, on_change, add_widget):
        self._on_change = on_change
        self._add_widget = add_widget

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

    def checkbox(self, name, value, label):
        checkbox = QCheckBox(label)
        checkbox.setChecked(value)
        self._add_widget(checkbox)
        checkbox.toggled.connect(
            lambda checked: self._on_change(name, checked)
        )
        return value

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
    def __init__(self, on_change, add_widget):
        self.elements = UIElements(on_change, add_widget)

    def slider(self, *args, **kwargs):
        return self.elements.slider(*args, **kwargs)

    def checkbox(self, *args, **kwargs):
        return self.elements.checkbox(*args, **kwargs)

    def input(self, *args, **kwargs):
        return self.elements.input(*args, **kwargs)

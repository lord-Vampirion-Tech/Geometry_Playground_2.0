from .elements import UIElementFactory
from .layouts import UILayouts


class ParameterAPI:
    def __init__(self, window, root_layout, create_widgets=False):
        self.window = window
        self.values = {}
        self.create_widgets = create_widgets

        self.layouts = UILayouts(
            root_layout,
            enabled=create_widgets,
            root_add_widget=window.add_parameter_widget,
        )
        self.elements = UIElementFactory(
            self._on_change,
            self.layouts.add_widget,
        )

    def _validate_name(self, name):
        if not isinstance(name, str) or not name.isidentifier():
            raise ValueError(f"Некорректное имя параметра: {name}")

    def slider(
        self,
        name,
        min=0,
        max=100,
        value=50,
        step=1,
        label=None,
    ):
        self._validate_name(name)

        if step <= 0 or max <= min:
            raise ValueError(f"Некорректный диапазон ползунка: {name}")

        count = round((max - min) / step)
        if count <= 0:
            raise ValueError(f"Некорректный диапазон ползунка: {name}")

        if self.create_widgets:
            initial_value = self.elements.slider(
                name, min, max, value, step, label or name
            )
        else:
            maximum_value = min + count * step
            initial_value = max(min, min(maximum_value, value))
            index = round((initial_value - min) / step)
            initial_value = min + index * step

        self.values[name] = initial_value
        return initial_value

    def checkbox(self, name, value=False, label=None):
        self._validate_name(name)
        if not isinstance(value, bool):
            raise TypeError(f"Значение checkbox «{name}» должно быть bool")

        self.values[name] = value
        if self.create_widgets:
            self.elements.checkbox(name, value, label or name)
        return value

    def input(
        self,
        name,
        value=0,
        type=float,
        min=None,
        max=None,
        step=None,
        decimals=6,
        label=None,
    ):
        self._validate_name(name)

        if type not in (int, float):
            raise TypeError("type должен быть int или float")
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"Значение input «{name}» должно быть числом")
        if min is not None and (isinstance(min, bool) or not isinstance(min, (int, float))):
            raise TypeError("min должен быть числом")
        if max is not None and (isinstance(max, bool) or not isinstance(max, (int, float))):
            raise TypeError("max должен быть числом")
        if min is not None and max is not None and min > max:
            raise ValueError("min не может быть больше max")
        if decimals < 0 or not isinstance(decimals, int):
            raise ValueError("decimals должен быть целым числом не меньше нуля")

        if step is None:
            step = 1 if type is int else 0.1
        if isinstance(step, bool) or not isinstance(step, (int, float)) or step <= 0:
            raise ValueError("step должен быть положительным числом")
        if type is int and (not float(step).is_integer()):
            raise ValueError("Для type=int шаг должен быть целым числом")

        if type is int:
            if not float(value).is_integer():
                raise ValueError("Для type=int значение должно быть целым")
            for bound_name, bound in (("min", min), ("max", max)):
                if bound is not None and not float(bound).is_integer():
                    raise ValueError(f"{bound_name} для type=int должен быть целым")
            initial_value = int(value)
            step = int(step)
        else:
            initial_value = float(value)

        if min is not None and initial_value < min:
            initial_value = min
        if max is not None and initial_value > max:
            initial_value = max

        if type is float:
            initial_value = round(initial_value, decimals)

        if self.create_widgets:
            initial_value = self.elements.input(
                name,
                initial_value,
                type,
                min,
                max,
                step,
                decimals,
                label or name,
            )

        self.values[name] = initial_value
        return initial_value

    def _on_change(self, name, value):
        self.values[name] = value
        self.window._on_parameter_changed(name, value)

    def column(self, spacing=6, margins=0):
        return self.layouts.column(spacing=spacing, margins=margins)

    def row(self, spacing=8, margins=0):
        return self.layouts.row(spacing=spacing, margins=margins)

    def grid(self, columns=2, spacing=8, row_spacing=None, margins=0):
        return self.layouts.grid(
            columns=columns,
            spacing=spacing,
            row_spacing=row_spacing,
            margins=margins,
        )

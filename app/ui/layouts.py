from contextlib import contextmanager

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)


class UILayouts:
    def __init__(self, root_layout, enabled=True):
        self._root_layout = root_layout
        self._enabled = enabled
        self._stack = [root_layout]

    def add_widget(self, widget):
        if self._enabled:
            self._stack[-1].addWidget(widget)

    @contextmanager
    def column(self, spacing=6, margins=0):
        with self._group(QVBoxLayout, spacing, margins):
            yield

    @contextmanager
    def row(self, spacing=8, margins=0):
        with self._group(QHBoxLayout, spacing, margins):
            yield

    @contextmanager
    def grid(self, columns=2, spacing=8, row_spacing=None, margins=0):
        if not isinstance(columns, int) or columns < 1:
            raise ValueError("columns должно быть целым числом больше нуля")

        with self._group(
            QGridLayout,
            spacing,
            margins,
            columns=columns,
            row_spacing=row_spacing,
        ):
            yield

    @contextmanager
    def _group(
        self,
        layout_type,
        spacing,
        margins,
        columns=None,
        row_spacing=None,
    ):
        if not self._enabled:
            yield
            return

        container = QWidget()
        layout = layout_type(container)
        layout.setContentsMargins(margins, margins, margins, margins)

        if layout_type is QGridLayout:
            layout.setHorizontalSpacing(spacing)
            layout.setVerticalSpacing(
                spacing if row_spacing is None else row_spacing
            )
            state = {"index": 0, "columns": columns}

            class GridLayoutProxy:
                def addWidget(self, widget):
                    index = state["index"]
                    row, column = divmod(index, state["columns"])
                    layout.addWidget(widget, row, column)
                    state["index"] += 1

            target_layout = GridLayoutProxy()
        else:
            layout.setSpacing(spacing)
            target_layout = layout

        self._stack[-1].addWidget(container)
        self._stack.append(target_layout)

        try:
            yield
        finally:
            self._stack.pop()

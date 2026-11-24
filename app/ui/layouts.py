from contextlib import contextmanager

from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
)


class UILayouts:
    def __init__(self, root_layout, enabled=True, root_add_widget=None, border_width=5, border_color="#000000"):
        self._root_layout = root_layout
        self._enabled = enabled
        self._root_add_widget = root_add_widget or root_layout.addWidget
        self._stack = [root_layout]
        self._groups = []
        self._border_width = max(0, int(border_width))
        self._border_color = border_color

    def _add_to_current(self, widget):
        if len(self._stack) == 1:
            self._root_add_widget(widget)
        else:
            self._stack[-1].addWidget(widget)

    def add_widget(self, widget):
        if self._enabled:
            self._add_to_current(widget)

    def set_group_style(self, border_width, border_color):
        self._border_width = max(0, int(border_width))
        self._border_color = border_color
        for container in self._groups:
            self._apply_group_style(container)

    def _apply_group_style(self, container):
        container.setStyleSheet(
            "QFrame#uiGroupContainer { "
            f"border: {self._border_width}px solid {self._border_color}; "
            "}"
        )

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

        container = QFrame()
        container.setObjectName("uiGroupContainer")
        self._groups.append(container)
        self._apply_group_style(container)
        layout = layout_type(container)
        content_margin = margins + self._border_width
        layout.setContentsMargins(
            content_margin,
            content_margin,
            content_margin,
            content_margin,
        )

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

        self._add_to_current(container)
        self._stack.append(target_layout)

        try:
            yield
        finally:
            self._stack.pop()

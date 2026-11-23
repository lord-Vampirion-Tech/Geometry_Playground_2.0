
from PySide6.QtWidgets import (
    QPlainTextEdit, 
    QTextEdit,
    QWidget
)

from PySide6.QtGui import (
    QFont,
    QColor,
    QTextCharFormat,
    QSyntaxHighlighter,
    QPainter,
    QTextCursor
)

from PySide6.QtCore import (
    Qt,
    QRect,
    QSize,
    QRegularExpression
)


class PythonHighlighter(QSyntaxHighlighter):

    def __init__(self, document):
        super().__init__(document)

        self.rules = []

        def add_rule(pattern, color, bold=False):
            fmt = QTextCharFormat()
            fmt.setForeground(QColor(color))

            if bold:
                fmt.setFontWeight(QFont.Weight.Bold)

            self.rules.append((
                QRegularExpression(pattern),
                fmt
            ))

        # Python keywords
        add_rule(
            r"\b(def|class|return|if|else|elif|for|in|import|from|as|"
            r"True|False|None|and|or|not|while|break|continue|pass|"
            r"try|except|finally|raise|with|lambda|yield|global|"
            r"nonlocal|assert|del|is|async|await)\b",
            "#c792ea",
            True
        )

        # Geometry API
        add_rule(
            r"\b(New_SQUAER|New_CUBE|New_BOUNDS|setPos|setColor|"
            r"setRot|setSize|setOpacity|movePoint|getPoint|"
            r"update|Time|loop)\b",
            "#82aaff",
            True
        )

        # Strings
        add_rule(
            r'"[^"\n]*"|\'[^\'\n]*\'',
            "#c3e88d"
        )

        # Numbers
        add_rule(
            r"\b\d+(\.\d+)?\b",
            "#f78c6c"
        )

        # Hex colors
        add_rule(
            r"#[0-9a-fA-F]{6}\b",
            "#35c848"
        )

        # Comments
        add_rule(
            r"#.*",
            "#697386"
        )

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            matches = pattern.globalMatch(text)

            while matches.hasNext():
                match = matches.next()

                self.setFormat(
                    match.capturedStart(),
                    match.capturedLength(),
                    fmt
                )


class LineNumberArea(QWidget):

    def __init__(self, editor):
        super().__init__(editor)

        self.editor = editor

    def sizeHint(self):
        return QSize(
            self.editor.line_number_area_width(),
            0
        )

    def paintEvent(self, event):
        self.editor.line_number_area_paint_event(event)


class CodeEditor(QPlainTextEdit):

    INDENT = "    "

    def __init__(self, parent=None):
        super().__init__(parent)

        font = QFont("Consolas", 12)
        font.setStyleHint(QFont.StyleHint.Monospace)

        self.setFont(font)

        self.setTabStopDistance(
            4 * self.fontMetrics().horizontalAdvance(" ")
        )

        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #171b24;
                color: #d6deeb;
                border: none;
                selection-background-color: #35445e;
                padding: 10px;
            }
        """)

        self.highlighter = PythonHighlighter(
            self.document()
        )

        self.line_number_area = LineNumberArea(self)

        self._error_line = None

        self.blockCountChanged.connect(
            self.update_line_number_area_width
        )

        self.updateRequest.connect(
            self.update_line_number_area
        )

        self.cursorPositionChanged.connect(
            self.highlight_current_line
        )

        self.update_line_number_area_width()
        self.highlight_current_line()

    # ==================================================
    # Номера строк
    # ==================================================

    def line_number_area_width(self):

        digits = max(
            2,
            len(str(max(1, self.blockCount())))
        )

        return (
            12
            + self.fontMetrics().horizontalAdvance("9") * digits
        )

    def update_line_number_area_width(self, *_):

        self.setViewportMargins(
            self.line_number_area_width(),
            0,
            0,
            0
        )

    def update_line_number_area(self, rect, dy):

        if dy:
            self.line_number_area.scroll(0, dy)

        else:
            self.line_number_area.update(
                0,
                rect.y(),
                self.line_number_area.width(),
                rect.height()
            )

        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width()

    def resizeEvent(self, event):

        super().resizeEvent(event)

        contents = self.contentsRect()

        self.line_number_area.setGeometry(
            QRect(
                contents.left(),
                contents.top(),
                self.line_number_area_width(),
                contents.height()
            )
        )

    def line_number_area_paint_event(self, event):

        painter = QPainter(self.line_number_area)

        painter.fillRect(
            event.rect(),
            QColor("#131720")
        )

        block = self.firstVisibleBlock()

        block_number = block.blockNumber()

        top = int(
            self.blockBoundingGeometry(block)
            .translated(self.contentOffset())
            .top()
        )

        bottom = top + int(
            self.blockBoundingRect(block).height()
        )

        while block.isValid() and top <= event.rect().bottom():

            if block.isVisible() and bottom >= event.rect().top():

                number = str(block_number + 1)

                color = (
                    QColor("#ff7777")
                    if self._error_line == block_number + 1
                    else QColor("#697386")
                )

                if block == self.textCursor().block():
                    color = QColor("#d6deeb")

                painter.setPen(color)

                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number
                )

            block = block.next()

            top = bottom

            if block.isValid():
                bottom = top + int(
                    self.blockBoundingRect(block).height()
                )

            block_number += 1

    # ==================================================
    # Подсветка текущей строки и ошибок
    # ==================================================

    def highlight_current_line(self):

        selections = []

        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()

            selection.format.setBackground(
                QColor("#202633")
            )

            selection.format.setProperty(
                QTextCharFormat.Property.FullWidthSelection,
                True
            )

            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()

            selections.append(selection)

        if self._error_line is not None:

            block = self.document().findBlockByNumber(
                self._error_line - 1
            )

            if block.isValid():

                selection = QPlainTextEdit.ExtraSelection()

                selection.format.setBackground(
                    QColor("#592b35")
                )

                selection.format.setProperty(
                    QTextCharFormat.Property.FullWidthSelection,
                    True
                )

                selection.cursor = QTextCursor(block)
                selection.cursor.clearSelection()

                selections.append(selection)

        self.setExtraSelections(selections)

        self.line_number_area.update()

    def set_error_line(self, line):

        self._error_line = (
            int(line)
            if line is not None and int(line) > 0
            else None
        )

        self.highlight_current_line()

        if self._error_line is not None:

            block = self.document().findBlockByNumber(
                self._error_line - 1
            )

            if block.isValid():
                cursor = QTextCursor(block)
                self.setTextCursor(cursor)
                self.centerCursor()

    def clear_error(self):
        self.set_error_line(None)

    # ==================================================
    # Работа с выделенными строками
    # ==================================================

    def _selected_blocks(self):

        cursor = self.textCursor()

        start = cursor.selectionStart()
        end = cursor.selectionEnd()

        first = self.document().findBlock(start)
        last = self.document().findBlock(end)

        if (
            last != first
            and end == last.position()
        ):
            last = last.previous()

        blocks = []

        block = first

        while block.isValid():

            blocks.append(block)

            if block == last:
                break

            block = block.next()

        return blocks, start, end

    def _restore_selection(self, start, end):

        cursor = self.textCursor()

        cursor.setPosition(start)
        cursor.setPosition(
            end,
            QTextCursor.MoveMode.KeepAnchor
        )

        self.setTextCursor(cursor)

    # ==================================================
    # Отступы
    # ==================================================

    def indent_selection(self, remove=False):

        cursor = self.textCursor()

        if not cursor.hasSelection() and not remove:
            cursor.insertText(self.INDENT)
            return

        blocks, start, end = self._selected_blocks()

        delta = 0

        cursor.beginEditBlock()

        for block in reversed(blocks):

            position = block.position()
            text = block.text()

            cursor.setPosition(position)

            if remove:

                count = len(text) - len(text.lstrip(" "))
                count = min(4, count)

                if count > 0:
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        count
                    )

                    cursor.removeSelectedText()
                    delta -= count

            else:

                cursor.insertText(self.INDENT)
                delta += 4

        cursor.endEditBlock()

        self._restore_selection(
            start,
            max(start, end + delta)
        )

    # ==================================================
    # Комментирование
    # ==================================================

    def toggle_comment(self):

        blocks, start, end = self._selected_blocks()

        if not blocks:
            return

        all_commented = all(
            block.text().lstrip().startswith("#")
            for block in blocks
            if block.text().strip()
        )

        delta = 0

        cursor = self.textCursor()
        cursor.beginEditBlock()

        for block in reversed(blocks):

            text = block.text()

            if not text.strip():
                continue

            indent = len(text) - len(text.lstrip())
            position = block.position() + indent

            cursor.setPosition(position)

            if all_commented:

                if text[indent:indent + 2] == "# ":
                    cursor.movePosition(
                        QTextCursor.MoveOperation.Right,
                        QTextCursor.MoveMode.KeepAnchor,
                        2
                    )
                    cursor.removeSelectedText()
                    delta -= 2

                elif text[indent:indent + 1] == "#":
                    cursor.deleteChar()
                    delta -= 1

            else:

                cursor.insertText("# ")
                delta += 2

        cursor.endEditBlock()

        self._restore_selection(
            start,
            max(start, end + delta)
        )

    # ==================================================
    # Клавиатура
    # ==================================================

    def keyPressEvent(self, event):

        key = event.key()
        modifiers = event.modifiers()

        # Tab / Shift + Tab
        if key in (
            Qt.Key.Key_Tab,
            Qt.Key.Key_Backtab
        ):

            remove = (
                key == Qt.Key.Key_Backtab
                or bool(
                    modifiers & Qt.KeyboardModifier.ShiftModifier
                )
            )

            self.indent_selection(remove)
            return

        # Ctrl + /
        if (
            modifiers & Qt.KeyboardModifier.ControlModifier
            and event.text() == "/"
        ):

            self.toggle_comment()
            return

        super().keyPressEvent(event)

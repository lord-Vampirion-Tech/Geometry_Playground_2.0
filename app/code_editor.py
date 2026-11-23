from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QPlainTextEdit


class CodeEditor(QPlainTextEdit):
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        text = event.text()

        if modifiers & Qt.KeyboardModifier.ControlModifier and key == Qt.Key.Key_Slash:
            self.toggle_comment()
            return

        if key == Qt.Key.Key_Tab and not modifiers:
            if self.textCursor().hasSelection():
                self.change_indent(4)
            else:
                self.insertPlainText('    ')
            return

        if key == Qt.Key.Key_Backtab or (key == Qt.Key.Key_Tab and modifiers & Qt.KeyboardModifier.ShiftModifier):
            self.change_indent(-4)
            return

        pairs = {'(': ')', '{': '}', '[': ']', '"': '"', "'": "'"}
        if text in pairs and not modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier):
            self.wrap_selection(text, pairs[text])
            return

        super().keyPressEvent(event)

    def _selected_blocks(self):
        cursor = self.textCursor()
        start = cursor.selectionStart() if cursor.hasSelection() else cursor.position()
        end = cursor.selectionEnd() if cursor.hasSelection() else cursor.position()
        first = self.document().findBlock(start)
        last = self.document().findBlock(end if end > start else start)
        blocks = []
        block = first
        while block.isValid():
            blocks.append(block)
            if block == last:
                break
            block = block.next()
        return blocks

    def toggle_comment(self):
        blocks = self._selected_blocks()
        lines = [block.text() for block in blocks if block.text().strip()]
        uncomment = bool(lines) and all(line.lstrip().startswith('#') for line in lines)
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for block in reversed(blocks):
            line = block.text()
            if not line.strip():
                continue
            indent = len(line) - len(line.lstrip())
            cursor.setPosition(block.position() + indent)
            if uncomment:
                cursor.deleteChar()
                if cursor.document().characterAt(cursor.position()) == ' ':
                    cursor.deleteChar()
            else:
                cursor.insertText('# ')
        cursor.endEditBlock()

    def change_indent(self, amount):
        blocks = self._selected_blocks()
        cursor = self.textCursor()
        cursor.beginEditBlock()
        for block in reversed(blocks):
            line = block.text()
            if amount > 0:
                cursor.setPosition(block.position())
                cursor.insertText(' ' * amount)
            else:
                count = min(-amount, len(line) - len(line.lstrip(' ')))
                if count:
                    cursor.setPosition(block.position())
                    cursor.movePosition(QTextCursor.MoveOperation.Right, QTextCursor.MoveMode.KeepAnchor, count)
                    cursor.removeSelectedText()
        cursor.endEditBlock()

    def wrap_selection(self, opening, closing):
        cursor = self.textCursor()
        if cursor.hasSelection():
            selected = cursor.selectedText().replace('\u2029', '\n')
            start = cursor.selectionStart()
            cursor.insertText(opening + selected + closing)
            cursor.setPosition(start + len(opening))
            cursor.setPosition(start + len(opening) + len(selected), QTextCursor.MoveMode.KeepAnchor)
        else:
            cursor.insertText(opening + closing)
            cursor.movePosition(QTextCursor.MoveOperation.Left, QTextCursor.MoveMode.MoveAnchor, len(closing))
        self.setTextCursor(cursor)

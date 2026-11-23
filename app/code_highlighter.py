import keyword
import re

from PySide6.QtGui import QColor, QSyntaxHighlighter, QTextCharFormat


class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        self.keyword_format = self._format("#c792ea")
        self.function_format = self._format("#82aaff")
        self.variable_format = self._format("#f6c177")
        self.string_format = self._format("#a6da95")
        self.number_format = self._format("#f78c6c")
        self.comment_format = self._format("#697386")
        self.operator_format = self._format("#89ddff")

        self.keywords = set(keyword.kwlist)
        self.variable_names = set()
        self.function_names = set()
        self._refreshing_names = False

        document.contentsChanged.connect(self._refresh_names)
        self._refresh_names()

    @staticmethod
    def _format(color, bold=False):
        result = QTextCharFormat()
        result.setForeground(QColor(color))
        result.setFontWeight(700 if bold else 400)
        return result

    def _refresh_names(self):
        if self._refreshing_names:
            return

        self._refreshing_names = True
        try:
            source = self.document().toPlainText()

            variable_names = set(re.findall(
                r"(?m)^\\s*([A-Za-z_]\\w*)\\s*(?=(?:=|\\+=|-=|\\*=|/=|:=))",
                source
            ))

            function_names = set(re.findall(
                r"\\bdef\\s+([A-Za-z_]\\w*)",
                source
            ))

            if (
                variable_names == self.variable_names
                and function_names == self.function_names
            ):
                return

            self.variable_names = variable_names
            self.function_names = function_names
            self.rehighlight()
        finally:
            self._refreshing_names = False

    def _string_format(self, value):
        candidate = value.strip()

        prefix = re.match(r"(?i)^[rubf]{0,2}", candidate)
        if prefix:
            candidate = candidate[prefix.end():]

        if len(candidate) >= 2 and candidate[0] in "'\\"" and candidate[-1] == candidate[0]:
            candidate = candidate[1:-1]

        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", candidate):
            return self._format(candidate)

        if re.fullmatch(r"[A-Za-z]+", candidate) and QColor.isValidColor(candidate):
            return self._format(candidate)

        return self.string_format

    def highlightBlock(self, text):
        string_pattern = re.compile(
            r"""(?i)(?:[rubf]{0,2})(?:""" +
            r"""'''[\\s\\S]*?'''|""" +
            r'''"""[\\s\\S]*?"""|''' +
            r"""'(?:\\\\.|[^'\\\\])*'|""" +
            r'''"(?:\\\\.|[^"\\\\])*")'''
        )

        strings = []
        for match in string_pattern.finditer(text):
            strings.append((match.start(), match.end()))
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self._string_format(match.group())
            )

        def inside_string(position):
            return any(start <= position < end for start, end in strings)

        comment = re.search(r"#", text)
        if comment and not inside_string(comment.start()):
            self.setFormat(
                comment.start(),
                len(text) - comment.start(),
                self.comment_format
            )

        for match in re.finditer(r"\\b\\d+(?:\\.\\d+)?(?:[eE][+-]?\\d+)?\\b", text):
            if not inside_string(match.start()):
                self.setFormat(match.start(), len(match.group()), self.number_format)

        for match in re.finditer(r"\\b[A-Za-z_]\\w*\\b", text):
            start = match.start()
            name = match.group()

            if inside_string(start) or (comment and start >= comment.start()):
                continue

            if text[max(0, start - 1):start] == ".":
                continue

            if name in self.keywords:
                fmt = self.keyword_format
            elif name in self.function_names or re.match(r"\\s*\\(", text[match.end():]):
                fmt = self.function_format
            elif name in self.variable_names:
                fmt = self.variable_format
            else:
                continue

            self.setFormat(start, len(name), fmt)

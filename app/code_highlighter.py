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

        self.rules = [
            (re.compile(r"#[^\\n]*"), self.comment_format),
            (re.compile(r"\b\d+(?:\.\d+)?(?:[eE][+-]?\d+)?\b"), self.number_format),
            (re.compile(r"\b(?:and|or|not|is|in)\b|[+*/%=<>!-]+"), self.operator_format),
        ]

        document.contentsChanged.connect(self._refresh_names)
        self._refresh_names()

    @staticmethod
    def _format(color, bold=False, italic=False):
        result = QTextCharFormat()
        result.setForeground(QColor(color))
        result.setFontWeight(700 if bold else 400)
        result.setFontItalic(italic)
        return result

    def _refresh_names(self):
        source = self.document().toPlainText()

        self.variable_names = set(
            re.findall(
                r"(?m)^\s*([A-Za-z_]\w*)\s*(?=(?:=|\+=|-=|\*=|/=|:=))",
                source
            )
        )

        self.function_names = set(
            re.findall(r"\bdef\s+([A-Za-z_]\w*)", source)
        )

        self.rehighlight()

    def _string_format(self, value):
        color = None

        candidate = value.strip()
        if candidate.startswith(("'", '"')):
            candidate = candidate[1:-1]

        if re.fullmatch(r"#[0-9a-fA-F]{3,8}", candidate):
            color = candidate
        elif re.fullmatch(r"[A-Za-z]+", candidate) and QColor.isValidColor(candidate):
            color = candidate

        if color:
            return self._format(color)

        return self.string_format

    def highlightBlock(self, text):
        for pattern, text_format in self.rules:
            for match in pattern.finditer(text):
                self.setFormat(match.start(), match.end() - match.start(), text_format)

        string_pattern = re.compile(
            r"(?i)(?:[rubf]{0,2})(?:'''[\\s\\S]*?'''|\\\"\\\"\\\"[\\s\\S]*?\\\"\\\"\\\"|'(?:\\\\.|[^'\\\\])*'|\\\"(?:\\\\.|[^\\\"\\\\])*\\\")"
        )

        for match in string_pattern.finditer(text):
            self.setFormat(
                match.start(),
                match.end() - match.start(),
                self._string_format(match.group())
            )

        for match in re.finditer(r"\\b[A-Za-z_]\\w*\\b", text):
            name = match.group()
            start = match.start()

            if text[max(0, start - 1):start] == ".":
                continue

            if name in self.keywords:
                self.setFormat(start, len(name), self.keyword_format)
            elif name in self.function_names or re.match(r"\\s*\\(", text[match.end():]):
                self.setFormat(start, len(name), self.function_format)
            elif name in self.variable_names:
                self.setFormat(start, len(name), self.variable_format)

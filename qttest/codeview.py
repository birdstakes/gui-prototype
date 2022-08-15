from PyQt5 import QtCore, QtGui, QtWidgets


class Token:
    def __init__(self, text):
        self.text = text


def prop(default):
    val = [default]

    def setter(self, value):
        val[0] = value

    def getter(self):
        return val[0]

    return QtCore.pyqtProperty(type(default), getter, setter)


class WordHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent, color):
        super().__init__(parent)
        self.color = color
        self.regex = None

    def set_word(self, word):
        if word is None:
            self.regex = None
        else:
            self.regex = QtCore.QRegularExpression(f"\\b{word}\\b")
        self.rehighlight()

    def set_color(self, color):
        self.color = color

    def highlightBlock(self, text):
        if self.regex is None:
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(self.color)
        matches = self.regex.globalMatch(text)
        while matches.hasNext():
            match = matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class CodeViewWidget(QtWidgets.QTextEdit):
    defaultColor = prop(QtGui.QColor("black"))
    highlightColor = prop(QtGui.QColor("yellow"))

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            self.textInteractionFlags() | QtCore.Qt.TextSelectableByKeyboard
        )
        self.viewport().setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.highlighter = WordHighlighter(self.document(), self.highlightColor)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.lines = []

    def changeEvent(self, e):
        if e.type() == QtCore.QEvent.StyleChange:
            self.highlighter.set_color(self.highlightColor)
            self.update_text()
        else:
            super().changeEvent(e)

    def set_content(self, lines):
        self.lines = lines
        self.update_text()

    def update_text(self):
        self.tokens = []
        self.clear()

        for line in self.lines:
            for token in line:
                if token.type is not None:
                    pos = self.textCursor().position()
                    self.tokens.append(((pos, pos + len(token.text)), token))
                    self.setTextColor(self.token_color(token))
                else:
                    self.setTextColor(self.defaultColor)
                self.insertPlainText(token.text)
            self.insertPlainText("\n")

    def token_color(self, token):
        return self.defaultColor

    def on_cursor_position_changed(self):
        self.highlight_word_under_cursor()

    def highlight_word_under_cursor(self):
        is_word = lambda s: all(c.isalnum() or c == "_" for c in s)

        cursor = self.textCursor()

        char = self.document().characterAt(cursor.position())
        if char is None or not is_word(char):
            self.highlighter.set_word(None)
            return

        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        if is_word(word):
            self.highlighter.set_word(word)
        else:
            self.highlighter.set_word(None)

    def token_at(self, pos):
        lo, hi = 0, len(self.tokens)
        while lo < hi:
            mid = (lo + hi) // 2
            span, _ = self.tokens[mid]
            if pos < span[0]:
                hi = mid
            else:
                lo = mid + 1

        if lo == 0:
            return None

        span, token = self.tokens[lo - 1]
        if span[0] <= pos < span[1]:
            return token

        return None

import logging
from PyQt5 import QtCore, QtGui, QtWidgets


class Token:
    def __init__(self, text, type=None, data=None):
        self.text = text
        self.type = type
        self.data = data


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
    typeColor = prop(QtGui.QColor("blue"))
    identColor = prop(QtGui.QColor("green"))
    numColor = prop(QtGui.QColor("red"))
    highlightColor = prop(QtGui.QColor("yellow"))

    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            self.textInteractionFlags() | QtCore.Qt.TextSelectableByKeyboard
        )
        self.viewport().setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.set_content()
        self.highlighter = WordHighlighter(self.document(), self.highlightColor)
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)

    def changeEvent(self, e):
        if e.type() == QtCore.QEvent.StyleChange:
            self.highlighter = WordHighlighter(self.document(), self.highlightColor)
            self.set_content()
        else:
            super().changeEvent(e)

    def set_content(self):
        lines = [
            [Token("int", "type"), Token(" "), Token("main", "ident"), Token("() {")],
            [Token("    // return return return")],
            [Token("    return "), Token("123", "num"), Token(";")],
            [Token("}")],
        ]

        self.tokens = []
        self.clear()

        for line in lines:
            for token in line:
                if token.type is not None:
                    pos = self.textCursor().position()
                    self.tokens.append(((pos, pos + len(token.text)), token.data))
                    self.setTextColor(self.token_color(token.type))
                else:
                    self.setTextColor(self.defaultColor)
                self.insertPlainText(token.text)
            self.insertPlainText("\n")

    def token_color(self, token_type):
        return {
            "type": self.typeColor,
            "ident": self.identColor,
            "num": self.numColor,
        }.get(token_type, self.defaultColor)

    def on_cursor_position_changed(self):
        self.highlight_word_under_cursor()

        token = self.token_at(self.textCursor().position())
        if token is not None:
            logging.info(token)

    def highlight_word_under_cursor(self):
        cursor = self.textCursor()
        cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
        word = cursor.selectedText()
        if word.isalnum():
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

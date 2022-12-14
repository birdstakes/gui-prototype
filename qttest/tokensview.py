from PyQt5 import QtCore, QtGui, QtWidgets


class WordHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent, color=QtGui.QColor("yellow")):
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


class TokensViewWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            self.textInteractionFlags() | QtCore.Qt.TextSelectableByKeyboard
        )
        self.viewport().setCursor(QtCore.Qt.CursorShape.ArrowCursor)
        self.highlighter = WordHighlighter(self.document())
        self.cursorPositionChanged.connect(self.on_cursor_position_changed)
        self.lines = []

    def set_content(self, lines):
        self.lines = lines
        self.update_text()

    def update_text(self):
        old_position = self.textCursor().position()

        self.tokens = []
        self.clear()

        for line in self.lines:
            for token in line:
                pos = self.textCursor().position()
                self.tokens.append(((pos, pos + len(token.text)), token))
                self.setTextColor(self.token_color(token))
                self.insertPlainText(token.text)
            self.insertPlainText("\n")

        if old_position < len(self.toPlainText()):
            cursor = self.textCursor()
            cursor.setPosition(old_position)
            self.setTextCursor(cursor)

    def token_color(self, token):
        return QtGui.QColor("black")

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

    def current_token(self):
        return self.token_at(self.textCursor().position())

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

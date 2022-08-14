import logging
from PyQt5 import QtCore, QtGui, QtWidgets


class WordHighlighter(QtGui.QSyntaxHighlighter):
    def __init__(self, parent, word=None):
        super().__init__(parent)
        self.set_word(word)

    def set_word(self, word):
        if word is None:
            self.regex = None
        else:
            # TODO make sure word is properly escaped
            self.regex = QtCore.QRegularExpression(f"\\b{word}\\b")
        self.rehighlight()

    def highlightBlock(self, text):
        if self.regex is None:
            return
        fmt = QtGui.QTextCharFormat()
        fmt.setBackground(QtGui.QColorConstants.Gray)
        matches = self.regex.globalMatch(text)
        while matches.hasNext():
            match = matches.next()
            self.setFormat(match.capturedStart(), match.capturedLength(), fmt)


class CodeViewWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()

        red = {"color": "red", "coolness": 0}
        green = {"color": "green", "coolness": 1}
        blue = {"color": "blue", "coolness": 2}

        lines = [
            [("int", red), (" ", None), ("main", green), ("() {", None)],
            [("return return return", None)],
            [("    return ", None), ("123", blue), (";", None)],
            [("}", None)],
        ]

        self.tokens = []

        # TODO does qt provide a way to programmatically generate html?
        html = "<pre>"
        pos = 0
        for line in lines:
            for token, data in line:
                if data is not None:
                    self.tokens.append(((pos, pos + len(token)), data))
                    # TODO instead of style, change class based on token type and let css choose color etc.
                    color = data["color"]
                    html += f'<span style="color: {color}">{token}</span>'
                else:
                    html += f"<span>{token}</span>"
                pos += len(token)
            html += "\n"
            pos += 1
        html += "</pre>"

        self.setReadOnly(True)
        self.setTextInteractionFlags(
            self.textInteractionFlags() | QtCore.Qt.TextSelectableByKeyboard
        )
        self.setHtml(html)

        self.highlighter = WordHighlighter(self.document())

        def f():
            cursor = self.textCursor()
            cursor.select(QtGui.QTextCursor.SelectionType.WordUnderCursor)
            self.highlighter.set_word(cursor.selectedText())

            token = self.token_at(self.textCursor().position())
            if token is not None:
                logging.info(token)

        self.cursorPositionChanged.connect(f)

    def token_at(self, pos):
        for span, token in self.tokens:
            if span[0] <= pos < span[1]:
                return token
        return None

import logging
from PyQt5 import QtGui

from .codeview import CodeViewWidget, Token, prop


class DecompilerToken(Token):
    def __init__(self, text, type=None, data=None):
        self.text = text
        self.type = type
        self.data = data


class DecompilerWidget(CodeViewWidget):
    typeColor = prop(QtGui.QColor("blue"))
    identColor = prop(QtGui.QColor("green"))
    numColor = prop(QtGui.QColor("red"))

    def __init__(self):
        super().__init__()

        lines = [
            [
                DecompilerToken("int", "type"),
                DecompilerToken(" "),
                DecompilerToken("main", "ident"),
                DecompilerToken("() {"),
            ],
            [DecompilerToken("    // return return return")],
            [
                DecompilerToken("    return "),
                DecompilerToken("123", "num"),
                DecompilerToken(";"),
            ],
            [DecompilerToken("}")],
        ]
        self.set_content(lines)

    def token_color(self, token):
        return {
            "type": self.typeColor,
            "ident": self.identColor,
            "num": self.numColor,
        }.get(token.type, self.defaultColor)

    def on_cursor_position_changed(self):
        super().on_cursor_position_changed()

        token = self.token_at(self.textCursor().position())
        if token is not None:
            logging.info(token)

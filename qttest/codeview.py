from PyQt5 import QtCore, QtGui, QtWidgets

from .tokensview import TokensViewWidget, prop


class CodeViewWidget(TokensViewWidget):
    def __init__(self):
        super().__init__()
        self.analysis = None
        self.function = None

    def update(self, function):
        raise NotImplementedError

    def set_analysis(self, analysis):
        if self.function is not None:
            self.function.code_changed.unwatch(self.update)
        self.analysis = analysis
        self.function = None

    def set_function(self, function):
        if self.function is not None:
            self.function.code_changed.unwatch(self.update)

        self.function = function
        self.function.code_changed.watch(self.update)
        self.update(function)

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_N:
            token = self.current_token()
            if token is None or not hasattr(token.item, "rename"):
                return
            name, ok = QtWidgets.QInputDialog.getText(self, "Rename", "Name:")
            if ok:
                if not token.item.rename(name):
                    QtWidgets.QMessageBox.warning(
                        self, "Rename failed", f"Could not rename {token.item.name()}"
                    )
        else:
            super().keyPressEvent(e)


class DecompilerWidget(CodeViewWidget):
    typeColor = prop(QtGui.QColor("blue"))
    identColor = prop(QtGui.QColor("green"))
    numColor = prop(QtGui.QColor("red"))

    def update(self, function):
        self.set_content(self.function.decompilation())

    def token_color(self, token):
        return {
            "type": self.typeColor,
            "ident": self.identColor,
            "num": self.numColor,
        }.get(token.type, self.defaultColor)


class DisassemblyWidget(CodeViewWidget):
    defaultColor = prop(QtGui.QColor("grey"))
    typeColor = prop(QtGui.QColor("blue"))
    identColor = prop(QtGui.QColor("green"))
    numColor = prop(QtGui.QColor("red"))
    opcodeColor = prop(QtGui.QColor("darkorange"))

    def update(self, function):
        self.set_content(self.function.disassembly())

    def token_color(self, token):
        return {
            "type": self.typeColor,
            "ident": self.identColor,
            "num": self.numColor,
            "opcode": self.opcodeColor,
        }.get(token.type, self.defaultColor)

from PyQt5 import QtCore, QtGui, QtWidgets

from .tokensview import TokensViewWidget


class CodeViewWidget(TokensViewWidget):
    def __init__(self):
        super().__init__()

        settings = QtCore.QSettings()
        self.colors = {
            "default": settings.value("codeview/default", QtGui.QColor("black")),
            "ident": settings.value("codeview/ident", QtGui.QColor("green")),
            "num": settings.value("codeview/num", QtGui.QColor("red")),
            "opcode": settings.value("codeview/opcode", QtGui.QColor("darkorange")),
            "type": settings.value("codeview/type", QtGui.QColor("blue")),
        }

        self.analysis = None
        self.function = None

    def token_color(self, token):
        return self.colors.get(token.type, self.colors["default"])

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
    def update(self, function):
        self.set_content(self.function.decompilation())


class DisassemblyWidget(CodeViewWidget):
    def update(self, function):
        self.set_content(self.function.disassembly())

import logging
import sys
from PyQt5 import QtCore, QtWidgets
from PyQtAds import ads

from .codeview import DecompilerWidget, DisassemblyWidget
from .dummy import Analysis, Function


class LogHandler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


class FunctionsListWidget(QtWidgets.QListWidget):
    selected = QtCore.pyqtSignal(Function)

    def __init__(self):
        super().__init__()
        self.functions = []
        self.currentItemChanged.connect(self.on_current_item_changed)

    def set_analysis(self, analysis):
        for function in self.functions:
            function.name_changed.unwatch(self.on_function_name_change)

        self.functions = analysis.functions()
        self.clear()
        for function in self.functions:
            self.addItem(function.name())
            function.name_changed.watch(self.on_function_name_change)

    def on_function_name_change(self, function):
        self.item(self.functions.index(function)).setText(function.name())

    def on_current_item_changed(self, current, previous):
        self.selected.emit(self.functions[self.indexFromItem(current).row()])


class ConsoleWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def log(self, message):
        self.append(message)


class MainWindow(QtWidgets.QMainWindow):
    new_analysis = QtCore.pyqtSignal(Analysis)
    goto = QtCore.pyqtSignal(Function)

    def __init__(self):
        super().__init__()

        self.settings = QtCore.QSettings(
            "settings.ini", QtCore.QSettings.Format.IniFormat
        )

        self.init_widgets()

        self.file_menu = self.menuBar().addMenu("File")
        self.view_menu = self.menuBar().addMenu("View")

        def add_menu_item(menu, name, function):
            action = QtWidgets.QAction(name, menu)
            action.triggered.connect(function)
            menu.addAction(action)

        add_menu_item(self.file_menu, "Open...", self.open)
        add_menu_item(self.file_menu, "Exit", QtWidgets.QApplication.quit)

        self.init_layout()

        self.view_menu.addSeparator()
        add_menu_item(self.view_menu, "Load layout...", self.load_layout)
        add_menu_item(self.view_menu, "Save layout...", self.save_layout)

        self.open()

    def init_widgets(self):
        self.console = ConsoleWidget()
        logging.getLogger().addHandler(LogHandler(self.console.log))

        self.functions = FunctionsListWidget()
        self.functions.selected.connect(self.goto)
        self.new_analysis.connect(self.functions.set_analysis)

        self.disassembly = DisassemblyWidget()
        self.goto.connect(self.disassembly.set_function)
        self.new_analysis.connect(self.disassembly.set_analysis)

        self.decompiler = DecompilerWidget()
        self.goto.connect(self.decompiler.set_function)
        self.new_analysis.connect(self.decompiler.set_analysis)

    def init_layout(self):
        ads.CDockManager.setConfigFlag(ads.CDockManager.OpaqueSplitterResize, True)
        self.dock_manager = ads.CDockManager(self)

        decompiler = self.register_dockable_widget("Decompiler", self.decompiler)
        functions = self.register_dockable_widget("Functions", self.functions)
        console = self.register_dockable_widget("Console", self.console)
        self.register_dockable_widget("Disassembly", self.disassembly)

        self.dock_manager.loadPerspectives(self.settings)
        if "Default" in self.dock_manager.perspectiveNames():
            self.dock_manager.openPerspective("Default")
        else:
            self.dock_manager.addDockWidget(ads.CenterDockWidgetArea, decompiler)

            area = self.dock_manager.addDockWidget(ads.LeftDockWidgetArea, functions)
            splitter = ads.internal.findParent(QtWidgets.QSplitter, area)
            splitter.setSizes((self.width() * 3 // 16, self.width() * 13 // 16))

            area = self.dock_manager.addDockWidget(ads.BottomDockWidgetArea, console)
            splitter = ads.internal.findParent(QtWidgets.QSplitter, area)
            splitter.setSizes((self.height() * 3 // 4, self.height() * 1 // 4))

            decompiler.toggleView(True)
            functions.toggleView(True)
            console.toggleView(True)

            self.dock_manager.addPerspective("Default")
            self.dock_manager.savePerspectives(self.settings)

    def register_dockable_widget(self, name, widget):
        dock_widget = ads.CDockWidget(name)
        dock_widget.setWidget(widget)
        self.view_menu.addAction(dock_widget.toggleViewAction())
        self.dock_manager.addDockWidgetFloating(dock_widget)
        dock_widget.toggleView(False)
        return dock_widget

    def open(self):
        analysis = Analysis()
        self.new_analysis.emit(analysis)
        self.goto.emit(analysis.functions()[0])

    def load_layout(self):
        self.dock_manager.loadPerspectives(self.settings)
        name, ok = QtWidgets.QInputDialog.getItem(
            self,
            "Load layout",
            "Layout:",
            self.dock_manager.perspectiveNames(),
            editable=False,
        )
        if ok:
            self.dock_manager.openPerspective(name)

    def save_layout(self):
        name, ok = QtWidgets.QInputDialog.getText(self, "Save layout", "Name:")
        if ok:
            self.dock_manager.addPerspective(name)
            self.dock_manager.savePerspectives(self.settings)


def main():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    app = QtWidgets.QApplication([])
    app.setStyleSheet(
        """
        CodeViewWidget {
            font-family: "Courier New";
        }
        """
    )

    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())


main()

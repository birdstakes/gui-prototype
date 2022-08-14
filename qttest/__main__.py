import logging
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQtAds import ads

from .codeview import CodeViewWidget


class Handler(logging.Handler):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback

    def emit(self, record):
        self.callback(self.format(record))


class FunctionsWidget(QtWidgets.QWidget):
    pass


class ConsoleWidget(QtWidgets.QTextEdit):
    def __init__(self):
        super().__init__()
        self.setReadOnly(True)

    def log(self, message):
        self.append(message)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()

        self.settings = QtCore.QSettings(
            "settings.ini", QtCore.QSettings.Format.IniFormat
        )

        self.console = ConsoleWidget()
        logging.getLogger().addHandler(Handler(self.console.log))

        self.file_menu = self.menuBar().addMenu("File")
        self.view_menu = self.menuBar().addMenu("View")

        def add_menu_item(menu, name, function):
            action = QtWidgets.QAction(name, menu)
            action.triggered.connect(function)
            menu.addAction(action)

        add_menu_item(self.file_menu, "Exit", QtWidgets.QApplication.quit)

        self.init_layout()

        self.view_menu.addSeparator()
        add_menu_item(self.view_menu, "Load layout...", self.load_layout)
        add_menu_item(self.view_menu, "Save layout...", self.save_layout)

    def init_layout(self):
        ads.CDockManager.setConfigFlag(ads.CDockManager.OpaqueSplitterResize, True)
        self.dock_manager = ads.CDockManager(self)

        decompiler = self.register_dockable_widget("Decompiler", CodeViewWidget())
        functions = self.register_dockable_widget("Functions", FunctionsWidget())
        console = self.register_dockable_widget("Console", self.console)

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

    main_window = MainWindow()
    main_window.resize(800, 600)
    main_window.show()

    sys.exit(app.exec())


main()

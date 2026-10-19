"""Qt Widgets application composition and desktop lifecycle."""

import sys

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication

from drlua import __version__
from drlua.ui.controller import AppController
from drlua.ui.desktop import ApplicationMutex
from drlua.ui.window import MainWindow


def run_application() -> int:
    app = QApplication([])
    app.setApplicationName("DrLua")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("DrLua")
    mutex = ApplicationMutex()
    controller = AppController()
    previous_excepthook = sys.excepthook

    def report_exception(exception_type, exception, tb):
        controller.reportException(exception_type, exception, tb)
        previous_excepthook(exception_type, exception, tb)

    sys.excepthook = report_exception
    window = MainWindow(controller)
    window.show()
    app.aboutToQuit.connect(controller.shutdown)
    result = app.exec()
    sys.excepthook = previous_excepthook
    del window
    mutex.close()
    if controller.setup_path is not None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(controller.setup_path)))
    return result

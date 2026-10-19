"""Qt Widgets application composition and desktop lifecycle."""

import os
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from drlua import __version__
from drlua.integrations import ICON_NAME
from drlua.ui.controller import AppController
from drlua.ui.desktop import ApplicationMutex
from drlua.ui.window import MainWindow


def run_application() -> int:
    app = QApplication([])
    app.setApplicationName("DrLua")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("DrLua")
    icon_root = Path(sys._MEIPASS) if getattr(sys, "frozen", False) else Path(__file__).resolve().parents[1]
    app.setWindowIcon(QIcon(str(icon_root / ICON_NAME)))
    mutex = ApplicationMutex()
    controller = AppController()
    if len(sys.argv) > 1:
        controller.form.sources = sys.argv[1]
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
    mutex.close()
    if window.pending_installer is not None:
        os.startfile(window.pending_installer)
    return result

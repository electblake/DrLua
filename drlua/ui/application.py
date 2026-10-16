"""Qt Quick application composition and desktop lifecycle."""

from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices, QFont, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle

from drlua import __version__
from drlua.ui.controller import AppController
from drlua.ui.desktop import ApplicationMutex


def create_engine(controller: AppController) -> QQmlApplicationEngine:
    engine = QQmlApplicationEngine()
    engine.setInitialProperties({"controller": controller})
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "Main.qml")))
    controller.installReady.connect(engine.rootObjects()[0].close)
    return engine


def run_application() -> int:
    app = QGuiApplication([])
    app.setApplicationName("DrLua")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("DrLua")
    font = QFont("Segoe UI")
    font.setPointSize(12)
    app.setFont(font)
    QQuickStyle.setStyle("FluentWinUI3")
    mutex = ApplicationMutex()
    controller = AppController()
    engine = create_engine(controller)
    app.aboutToQuit.connect(controller.shutdown)
    result = app.exec()
    del engine
    mutex.close()
    if controller.setup_path is not None:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(controller.setup_path)))
    return result

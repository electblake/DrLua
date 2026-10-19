from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from PySide6.QtWidgets import QApplication

from drlua.ui import application


@pytest.fixture(scope="session")
def qt_app():
    return QApplication.instance() or QApplication([])


@pytest.mark.parametrize("install", [False, True])
def test_installer_launch_follows_ui_shutdown_workers_and_mutex(monkeypatch, tmp_path, qt_app, install):
    monkeypatch.setattr(application.sys, "argv", ["drlua"])
    events = []
    setup = tmp_path / "DrLua-99.0.0-windows-amd64-Setup.exe"
    controller = SimpleNamespace(
        setup_path=setup, shutdown=lambda: events.append("workers finished")
    )
    app = Mock()
    app.aboutToQuit.connect.side_effect = lambda callback: setattr(
        app, "shutdown", callback
    )

    def execute():
        events.append("window closed")
        app.shutdown()
        return 0

    app.exec.side_effect = execute
    mutex = SimpleNamespace(close=lambda: events.append("mutex released"))
    monkeypatch.setattr(application, "QApplication", lambda args: app)
    monkeypatch.setattr(application, "AppController", lambda: controller)
    monkeypatch.setattr(application, "ApplicationMutex", lambda: mutex)
    monkeypatch.setattr(application, "MainWindow", lambda controller: Mock(pending_installer=setup if install else None))

    def launch(path):
        assert path == setup
        assert events == ["window closed", "workers finished", "mutex released"]
        events.append("installer launched")

    monkeypatch.setattr(application.os, "startfile", launch)
    assert application.run_application() == 0
    assert (events[-1] == "installer launched") is install


def test_explorer_directory_populates_form_before_window(monkeypatch, tmp_path, qt_app):
    from drlua.profile import Profile
    from drlua.ui.controller import AppController
    from drlua.ui.window import MainWindow

    app = qt_app
    folder = str(tmp_path / "Selected folder with spaces")
    monkeypatch.setattr(application.sys, "argv", ["drlua", folder])
    controller = AppController(user_profile=Profile(no_profile=True))
    monkeypatch.setattr(application, "AppController", lambda: controller)
    monkeypatch.setattr(application, "QApplication", lambda args: app)
    windows = []

    def window(controller):
        root = MainWindow(controller)
        windows.append(root)
        assert root.sources.toPlainText() == folder
        assert controller.form.sources == folder
        assert not controller.busy
        assert not controller._jobs
        assert not controller.generatedCommand
        return root

    monkeypatch.setattr(application, "MainWindow", window)
    monkeypatch.setattr(app, "exec", lambda: 0)
    assert application.run_application() == 0
    app.aboutToQuit.disconnect(controller.shutdown)
    controller.shutdown()
    windows[0].close()

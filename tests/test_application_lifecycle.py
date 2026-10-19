from types import SimpleNamespace
from unittest.mock import Mock

from drlua.ui import application


def test_installer_launch_follows_ui_shutdown_workers_and_mutex(monkeypatch, tmp_path):
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
    monkeypatch.setattr(application, "MainWindow", lambda controller: Mock())

    def launch(url):
        assert url.toLocalFile() == setup.as_posix()
        assert events == ["window closed", "workers finished", "mutex released"]
        events.append("installer launched")

    monkeypatch.setattr(application.QDesktopServices, "openUrl", launch)
    assert application.run_application() == 0
    assert events[-1] == "installer launched"

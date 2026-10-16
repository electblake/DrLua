from pathlib import Path
import threading
import time

import pytest
import shiboken6
from loguru import logger
from PySide6.QtCore import QPointF, QThread, QUrl, Qt, qInstallMessageHandler
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtQuick import QQuickItem
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtTest import QTest, QSignalSpy

from drlua.application import catalog, generation
from drlua.ui.application import create_engine
from drlua.ui.controller import AppController
from drlua import updates


@pytest.fixture(scope="module")
def app():
    app = QGuiApplication([])
    app.setFont(QFont("Segoe UI", 12))
    QQuickStyle.setStyle("FluentWinUI3")
    yield app


@pytest.fixture
def window(app, monkeypatch, tmp_path):
    monkeypatch.setattr(
        catalog,
        "SECTION_CATEGORY_DATA",
        {
            "Sections": {
                "Test section": {
                    "Path": str(tmp_path),
                    "Categories": {
                        "Test category": {
                            "Path": str(tmp_path / "category"),
                            "Tags": ["first", "second"],
                        },
                        "Other": {"Path": str(tmp_path / "other")},
                    },
                }
            },
        },
    )
    messages = []
    previous = qInstallMessageHandler(
        lambda kind, context, message: messages.append(message)
    )
    controller = AppController()
    engine = create_engine(controller)
    root = engine.rootObjects()[0]
    root.requestActivate()
    assert QTest.qWaitForWindowExposed(root)
    QTest.qWait(100)
    yield root, controller
    controller.shutdown()
    root.close()
    shiboken6.delete(engine)
    shiboken6.delete(controller)
    qInstallMessageHandler(previous)
    assert messages == []


def item(root, name):
    return root.findChild(QQuickItem, name)


def click(root, name):
    control = item(root, name)
    point = control.mapToScene(
        QPointF(control.width() / 2, control.height() / 2)
    ).toPoint()
    QTest.mouseClick(
        root, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point
    )


def wait_until(predicate):
    deadline = time.monotonic() + 30
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    assert predicate()


def test_sources_suggestions_and_editable_metadata(window, tmp_path):
    root, controller = window
    folder = tmp_path / "category"
    folder.mkdir()
    assert item(root, "sourcesField").hasActiveFocus()
    assert not item(root, "generateButton").isEnabled()
    controller.form.appendUrls([QUrl.fromLocalFile(str(folder))])
    controller.form.appendUrls([QUrl.fromLocalFile(str(tmp_path / "one.mp4"))])
    assert controller.form.name == "category"
    assert controller.form.section == "Test section"
    assert controller.form.category == "Test category"
    assert controller.form.tags == "first\nsecond"
    assert item(root, "generateButton").isEnabled()
    assert [
        Path(value)
        for value in item(root, "sourcesField").property("text").splitlines()
    ] == [folder, tmp_path / "one.mp4"]
    assert item(root, "categoryField").property("editText") == "Test category"
    controller.form.category = "Custom"
    assert item(root, "tagsField").property("text") == "Custom"


def test_real_generate_button_runs_media_off_ui_thread(window, monkeypatch, tmp_path):
    from drlua import create_bins

    root, controller = window
    monkeypatch.setattr(create_bins, "PROCESSED_DATA_DIR", tmp_path)
    sample = Path(__file__).resolve().parents[1] / "data" / "sample"
    controller.form.appendUrls([QUrl.fromLocalFile(str(sample))])
    controller.form.name = "Qt button integration"
    statuses = []
    threads = []
    original = generation.create_bins

    def generate(*args, **kwargs):
        threads.append(QThread.currentThread())
        return original(*args, **kwargs)

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.statusChanged.connect(lambda: statuses.append(controller.status))
    click(root, "generateButton")
    assert controller.busy
    assert not item(root, "generateButton").isEnabled()
    assert not item(root, "checkUpdatesButton").isEnabled()
    wait_until(lambda: not controller.busy)
    assert threads[0] != QGuiApplication.instance().thread()
    assert any("Probing media:" in status for status in statuses)
    assert "Lua script created:" in controller.status
    assert controller.progressValue == controller.progressMaximum
    assert item(root, "generateButton").isEnabled()
    generated = list((tmp_path / "create_bins").glob("*.lua"))
    assert len(generated) == 1
    assert "CreateBins(" in generated[0].read_text(encoding="utf-8")
    output = item(root, "outputText").property("text")
    assert "dofile([[" in output
    click(root, "copyOutputButton")
    assert QGuiApplication.clipboard().text() == output


def test_form_snapshot_stays_fixed_during_work(window, monkeypatch, tmp_path):
    root, controller = window
    started = threading.Event()
    proceed = threading.Event()
    received = []

    def generate(paths, **kwargs):
        received.append((paths, kwargs))
        started.set()
        proceed.wait(5)

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = f"{tmp_path}/one.mp4 | {tmp_path}/two.mp4"
    click(root, "nameField")
    controller.form.name = " Original "
    controller.form.group = " Group "
    controller.form.tags = "alpha, beta\ngamma"
    click(root, "generateButton")
    wait_until(started.is_set)
    controller.form.name = "Next run"
    proceed.set()
    wait_until(lambda: not controller.busy)
    assert received[0][1]["name"] == "Original"
    assert received[0][1]["group_name"] == "Group"
    assert received[0][1]["tag"] == ["alpha", "beta", "gamma"]
    assert len(received[0][0]) == 2


def test_output_signals_append_once(window):
    root, controller = window
    logger.info("First Qt update")
    logger.info("Second Qt update")
    QTest.qWait(50)
    text = item(root, "outputText").property("text")
    assert text.count("First Qt update") == 1
    assert text.count("Second Qt update") == 1


def test_keyboard_sources_and_resize(window, tmp_path):
    root, controller = window
    sources = item(root, "sourcesField")
    sources.forceActiveFocus()
    QGuiApplication.clipboard().setText(str(tmp_path))
    QTest.keyClick(root, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(root, Qt.Key.Key_Tab)
    assert controller.form.sources == str(tmp_path)
    assert controller.form.name == tmp_path.name
    assert item(root, "addFolderButton").hasActiveFocus()
    root.resize(700, 660)
    QTest.qWait(100)
    for name in (
        "generateButton",
        "checkUpdatesButton",
        "copyOutputButton",
        "openOutputButton",
    ):
        control = item(root, name)
        point = control.mapToScene(QPointF(0, 0))
        assert point.x() >= 0 and point.y() >= 0
        assert point.x() + control.width() <= root.width()
        assert point.y() + control.height() <= root.height()


def test_keyboard_metadata_and_repeated_suggestions(window):
    root, controller = window
    category = item(root, "categoryField")
    click(root, "categoryField")
    QGuiApplication.clipboard().setText("Typed category")
    QTest.keyClick(root, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(root, Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(root, Qt.Key.Key_Tab)
    assert controller.form.category == "Typed category"
    assert controller.form.tags == "Typed category"
    controller.form.category = "Test category"
    assert category.property("editText") == "Test category"
    assert item(root, "tagsField").property("text") == "first\nsecond"
    tags = item(root, "tagsField")
    tags.forceActiveFocus()
    QTest.qWait(50)
    position = tags.mapToScene(QPointF(0, 0))
    assert (
        position.y() + tags.height()
        < item(root, "outputText").mapToScene(QPointF(0, 0)).y()
    )
    QTest.keyClick(root, Qt.Key.Key_Tab)
    assert not tags.hasActiveFocus()


@pytest.mark.parametrize("scheme", [Qt.ColorScheme.Light, Qt.ColorScheme.Dark])
def test_scaled_layout_and_theme(window, app, scheme):
    root, controller = window
    app.styleHints().setColorScheme(scheme)
    root.setProperty("font", QFont("Segoe UI", 18))
    root.resize(1000, 880)
    QTest.qWait(200)
    screenshot = Path("build") / f"qt-{scheme.name.lower()}-large.png"
    screenshot.parent.mkdir(exist_ok=True)
    assert root.grabWindow().save(str(screenshot))
    for name in (
        "generateButton",
        "checkUpdatesButton",
        "openOutputButton",
        "copyOutputButton",
    ):
        control = item(root, name)
        position = control.mapToScene(QPointF(0, 0))
        assert position.x() >= 0 and position.y() >= 0
        assert position.x() + control.width() <= root.width()
        assert position.y() + control.height() <= root.height()
    app.styleHints().unsetColorScheme()


def test_current_update_keeps_form(window, monkeypatch, tmp_path):
    root, controller = window
    controller.form.sources = str(tmp_path)
    monkeypatch.setattr(
        updates, "latest_release", lambda: {"tag_name": controller.version}
    )
    click(root, "checkUpdatesButton")
    assert controller.busy
    wait_until(lambda: not controller.busy)
    assert "up to date" in controller.status
    assert controller.form.sources == str(tmp_path)


def test_update_prompt_declined_with_escape(window, monkeypatch):
    root, controller = window
    monkeypatch.setattr(updates, "latest_release", lambda: {"tag_name": "v99.0.0"})
    offered = QSignalSpy(controller.updateAvailable)
    click(root, "checkUpdatesButton")
    wait_until(lambda: offered.count() == 1)
    QTest.qWait(200)
    QTest.keyClick(root, Qt.Key.Key_Escape)
    wait_until(lambda: not controller.busy)
    assert controller.status == "Update cancelled."


def test_update_download_signals_close_after_file_ready(window, monkeypatch, tmp_path):
    root, controller = window
    setup = tmp_path / "DrLua-99.0.0-windows-amd64-Setup.exe"
    monkeypatch.setattr(updates, "latest_release", lambda: {"tag_name": "v99.0.0"})

    def download(release):
        assert QThread.currentThread() != QGuiApplication.instance().thread()
        setup.write_bytes(b"test installer")
        return setup

    monkeypatch.setattr(updates, "download_setup", download)
    offered = QSignalSpy(controller.updateAvailable)
    ready = QSignalSpy(controller.installReady)
    controller.checkUpdates()
    wait_until(lambda: offered.count() == 1)
    controller.acceptUpdate()
    wait_until(lambda: ready.count() == 1)
    assert controller.setup_path == setup
    assert setup.read_bytes() == b"test installer"


def test_close_waits_for_active_worker(app, monkeypatch, tmp_path):
    controller = AppController()
    finished = threading.Event()

    def generate(*args, **kwargs):
        time.sleep(0.1)
        finished.set()

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = str(tmp_path)
    controller.generate()
    controller.shutdown()
    assert finished.is_set()
    shiboken6.delete(controller)

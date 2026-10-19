from pathlib import Path
import threading
import time

import pytest
import shiboken6
from loguru import logger
from PySide6.QtCore import QPoint, QThread, QUrl, Qt, qInstallMessageHandler
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication, QWidget, QFormLayout
from PySide6.QtTest import QTest, QSignalSpy

from drlua.application import catalog, generation
from drlua.ui.window import MainWindow
from drlua.profile import Profile
from drlua.ui.controller import AppController
from drlua import updates


@pytest.fixture(scope="module")
def app():
    app = QApplication.instance() or QApplication([])
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
    controller = AppController(user_profile=Profile(no_profile=True))
    controller.saveDirectory = str(tmp_path / "output")
    root = MainWindow(controller)
    root.show()
    root.activateWindow()
    assert QTest.qWaitForWindowExposed(root)
    QTest.qWait(100)
    yield root, controller
    controller.shutdown()
    root.close()
    shiboken6.delete(root)
    shiboken6.delete(controller)
    qInstallMessageHandler(previous)
    assert messages == []


def item(root, name):
    return root.findChild(QWidget, name)


def click(root, name):
    control = item(root, name)
    if name == "checkUpdatesButton":
        root.tabs.setCurrentWidget(root.settings_page)
    QTest.mouseClick(control, Qt.MouseButton.LeftButton)


def wait_until(predicate):
    deadline = time.monotonic() + 30
    while not predicate() and time.monotonic() < deadline:
        QTest.qWait(10)
    assert predicate()


def test_sources_suggestions_and_editable_metadata(window, tmp_path):
    root, controller = window
    folder = tmp_path / "category"
    folder.mkdir()
    assert item(root, "sourcesField").hasFocus()
    assert not item(root, "generateButton").isEnabled()
    controller.form.appendUrls([QUrl.fromLocalFile(str(folder))])
    controller.form.appendUrls([QUrl.fromLocalFile(str(tmp_path / "one.mp4"))])
    wait_until(lambda: not controller.form.inferencePending)
    assert controller.form.name == "category"
    assert controller.form.section == "Test section"
    assert controller.form.category == "Test category"
    assert controller.form.tags == "first\nsecond"
    assert item(root, "generateButton").isEnabled()
    assert [
        Path(value)
        for value in item(root, "sourcesField").toPlainText().splitlines()
    ] == [folder, tmp_path / "one.mp4"]
    assert item(root, "categoryField").currentText() == "Test category"
    controller.form.category = "Custom"
    assert item(root, "tagsField").toPlainText() == "Custom"


def test_real_generate_button_runs_media_off_ui_thread(window, monkeypatch, tmp_path):
    root, controller = window
    assert not item(root, "copyLuaCommandButton").isEnabled()
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
    assert not item(root, "copyLuaCommandButton").isEnabled()
    assert not item(root, "checkUpdatesButton").isEnabled()
    wait_until(lambda: not controller.busy)
    assert threads[0] != QGuiApplication.instance().thread()
    assert any("Probing media:" in status for status in statuses)
    assert "Lua script created:" in controller.status
    assert controller.progressValue == controller.progressMaximum
    assert item(root, "generateButton").isEnabled()
    generated = list((tmp_path / "output").glob("*.lua"))
    assert len(generated) == 1
    assert "CreateBins(" in generated[0].read_text(encoding="utf-8")
    assert item(root, "copyLuaCommandButton").isEnabled()
    click(root, "copyLuaCommandButton")
    assert QApplication.clipboard().text() == f"dofile([[{generated[0].as_posix()}]])"
    assert item(root, "statusLabel").text() == "Copied 1 command to clipboard."
    output = item(root, "outputText").toPlainText()
    assert "dofile([[" in output
    for activity in ("Starting generation", "Resolving source", "Inspecting source", "Locating FFprobe", "Probing file"):
        assert activity in output
    click(root, "copyOutputButton")
    assert QGuiApplication.clipboard().text() == output
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: root.files.count() == 1)
    assert root.files.item(0).text() == generated[0].name
    root.files.item(0).setSelected(True)
    click(root, "copySelectedCommandsButton")
    assert QApplication.clipboard().text() == f"dofile([[{generated[0].as_posix()}]])"
    root.tabs.setCurrentWidget(root.generate_page)
    controller.form.name = "Second run"
    controller.saveDirectory = str(tmp_path / "second output")
    click(root, "copyLuaCommandButton")
    assert QApplication.clipboard().text() == f"dofile([[{generated[0].as_posix()}]])"
    click(root, "generateButton")
    assert not item(root, "copyLuaCommandButton").isEnabled()
    assert controller.generatedCommand == ""
    wait_until(lambda: not controller.busy)
    second = list((tmp_path / "second output").glob("*.lua"))
    assert len(second) == 1
    assert item(root, "copyLuaCommandButton").isEnabled()
    click(root, "copyLuaCommandButton")
    assert QApplication.clipboard().text() == f"dofile([[{second[0].as_posix()}]])"


@pytest.mark.parametrize("recursive", [True, False])
def test_generate_includes_subdirectory_media_when_checked(window, tmp_path, recursive):
    root, controller = window
    source = tmp_path / "media"
    nested = source / "nested" / "deeper"
    nested.mkdir(parents=True)
    sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "h1.mp4"
    (source / "top.mp4").write_bytes(sample.read_bytes())
    (nested / "nested.mp4").write_bytes(sample.read_bytes())
    controller.form.sources = str(source)
    controller.form.name = "Recursive checkbox"
    checkbox = item(root, "recursiveCheckBox")
    assert checkbox.isChecked()
    if not recursive:
        checkbox.setFocus()
        QTest.keyClick(checkbox, Qt.Key.Key_Space)
    assert controller.form.recursive == recursive
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    generated = list((tmp_path / "output").glob("*.lua"))
    assert len(generated) == 1
    script = generated[0].read_text(encoding="utf-8")
    assert "top.mp4" in script
    assert ("nested.mp4" in script) == recursive


def test_recursive_checkbox_saved_and_restored(app, monkeypatch, tmp_path):
    from PySide6.QtCore import QSettings
    from drlua import profile as profile_module

    settings_file = tmp_path / "preferences.ini"
    monkeypatch.setattr(profile_module, "QSettings", lambda *args: QSettings(str(settings_file), QSettings.Format.IniFormat))
    for expected in (True, False, True):
        controller = AppController(user_profile=Profile())
        root = MainWindow(controller)
        assert root.recursive.isChecked() == expected
        assert controller.form.snapshot(tmp_path).recursive == expected
        QTest.keyClick(root.recursive, Qt.Key.Key_Space)
        assert Profile().recursive == (not expected)
        controller.shutdown()
        root.close()
        shiboken6.delete(root)
        shiboken6.delete(controller)


@pytest.mark.parametrize("stage", ["Scanning folder:", "Grouping ", "Writing Lua script:"])
def test_cancel_generation_discards_and_can_generate_again(window, monkeypatch, tmp_path, stage):
    root, controller = window
    sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "h1.mp4"
    source = tmp_path / "media"
    source.mkdir()
    (source / "clip.mp4").write_bytes(sample.read_bytes())
    controller.form.sources = str(source)
    controller.form.name = "Cancellation integration"
    reached = threading.Event()
    original = generation.create_bins

    def generate(*args, **kwargs):
        report = kwargs["activity"]

        def activity(message):
            report(message)
            if message.startswith(stage):
                reached.set()
                while not QThread.currentThread().isInterruptionRequested():
                    time.sleep(0.01)

        kwargs["activity"] = activity
        return original(*args, **kwargs)

    monkeypatch.setattr(generation, "create_bins", generate)
    assert root.generate_button.text() == "&Generate"
    assert root.copy_lua.text() == "&Copy"
    assert not root.cancel_button.isEnabled()
    click(root, "generateButton")
    wait_until(reached.is_set)
    assert root.cancel_button.isEnabled()
    click(root, "cancelButton")
    assert not root.cancel_button.isEnabled()
    wait_until(lambda: not controller.busy)
    assert controller.status == "Generation cancelled."
    assert not controller.generatedCommand
    assert not root.copy_lua.isEnabled()
    assert root.generate_button.isEnabled()
    assert not list((tmp_path / "output").glob("*"))
    monkeypatch.setattr(generation, "create_bins", original)
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    assert controller.generatedCommand
    assert len(list((tmp_path / "output").glob("*.lua"))) == 1


def test_cancel_writing_preserves_existing_script(window, monkeypatch, tmp_path):
    from drlua import create_bins as bins_module

    root, controller = window
    sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "h1.mp4"
    controller.form.sources = str(sample)
    controller.form.name = "Preserve existing output"
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    saved = next((tmp_path / "output").glob("*.lua"))
    saved.write_text("existing script", encoding="utf-8")
    entered = threading.Event()
    original = bins_module.luadata.serialize

    def serialize(*args, **kwargs):
        entered.set()
        while not QThread.currentThread().isInterruptionRequested():
            time.sleep(0.01)
        return original(*args, **kwargs)

    monkeypatch.setattr(bins_module.luadata, "serialize", serialize)
    click(root, "generateButton")
    wait_until(entered.is_set)
    click(root, "cancelButton")
    wait_until(lambda: not controller.busy)
    assert saved.read_text(encoding="utf-8") == "existing script"
    assert list((tmp_path / "output").iterdir()) == [saved]
    assert not controller.generatedCommand
    assert controller.status == "Generation cancelled."


def test_cancel_pending_metadata_discards_result(window, monkeypatch, tmp_path):
    from drlua.ui import form as form_module

    root, controller = window
    entered = threading.Event()

    def metadata(source):
        entered.set()
        while not QThread.currentThread().isInterruptionRequested():
            time.sleep(0.01)
        return source, "Discard this name", ("Test section", "Test category")

    monkeypatch.setattr(form_module, "source_metadata", metadata)
    controller.form.sources = str(tmp_path)
    click(root, "generateButton")
    wait_until(entered.is_set)
    click(root, "cancelButton")
    wait_until(lambda: not controller.busy)
    assert controller.form.name == ""
    assert not controller.form.inferencePending
    assert controller._pending_request is None
    assert root.generate_button.isEnabled()
    assert controller.status == "Generation cancelled."


def test_cancel_kills_active_probe(window, monkeypatch, tmp_path):
    import sys
    from PySide6.QtCore import QProcess
    from drlua import create_bins as bins_module

    root, controller = window
    sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "h1.mp4"
    controller.form.sources = str(sample)
    controller.form.name = "Cancel active probe"
    started = threading.Event()
    killed = threading.Event()

    class SlowProbe(QProcess):
        def start(self, program, arguments):
            super().start(sys.executable, ["-c", "import time; time.sleep(30)"])
            self.waitForStarted()
            started.set()

        def kill(self):
            super().kill()
            killed.set()

    monkeypatch.setattr(bins_module, "QProcess", SlowProbe)
    click(root, "generateButton")
    wait_until(started.is_set)
    click(root, "cancelButton")
    wait_until(lambda: not controller.busy)
    assert killed.is_set()
    assert controller.status == "Generation cancelled."
    assert not list((tmp_path / "output").glob("*.lua"))


def test_form_snapshot_stays_fixed_during_work(window, monkeypatch, tmp_path):
    root, controller = window
    started = threading.Event()
    proceed = threading.Event()
    received = []

    def generate(paths, **kwargs):
        received.append((paths, kwargs))
        started.set()
        proceed.wait(5)
        return kwargs["output_directory"] / "snapshot.lua"

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
    text = item(root, "outputText").toPlainText()
    assert text.count("First Qt update") == 1
    assert text.count("Second Qt update") == 1


def test_keyboard_sources_and_resize(window, tmp_path):
    root, controller = window
    sources = item(root, "sourcesField")
    sources.setFocus()
    QGuiApplication.clipboard().setText(str(tmp_path))
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
    assert Path(controller.form.sources) == tmp_path
    wait_until(lambda: not controller.form.inferencePending)
    assert controller.form.name == tmp_path.name
    assert item(root, "addFolderButton").hasFocus()
    root.resize(700, 660)
    QTest.qWait(100)
    for name in (
        "generateButton",
        "copyLuaCommandButton",
        "copyOutputButton",
        "openOutputButton",
    ):
        control = item(root, name)
        point = control.mapTo(root, QPoint(0, 0))
        assert point.x() >= 0 and point.y() >= 0
        assert point.x() + control.width() <= root.width()
        assert point.y() + control.height() <= root.height()


def test_keyboard_metadata_and_repeated_suggestions(window):
    root, controller = window
    category = item(root, "categoryField")
    click(root, "categoryField")
    QGuiApplication.clipboard().setText("Typed category")
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_V, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
    assert controller.form.category == "Typed category"
    assert controller.form.tags == "Typed category"
    controller.form.category = "Test category"
    assert category.currentText() == "Test category"
    assert item(root, "tagsField").toPlainText() == "first\nsecond"
    tags = item(root, "tagsField")
    tags.setFocus()
    QTest.qWait(50)
    visible = tags.visibleRegion().boundingRect()
    assert not visible.isEmpty()
    position = tags.mapTo(root, visible.bottomLeft())
    assert (
        position.y()
        < item(root, "outputText").mapTo(root, QPoint(0, 0)).y()
    )
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Tab)
    assert not tags.hasFocus()


@pytest.mark.parametrize("scheme", [Qt.ColorScheme.Light, Qt.ColorScheme.Dark])
def test_scaled_layout_and_theme(window, app, scheme):
    root, controller = window
    app.styleHints().setColorScheme(scheme)
    font = QFont(app.font())
    font.setPointSize(18)
    root.setFont(font)
    root.resize(1000, 880)
    QTest.qWait(200)
    screenshot = Path("build") / f"qt-{scheme.name.lower()}-large.png"
    screenshot.parent.mkdir(exist_ok=True)
    assert root.grab().save(str(screenshot))
    for name in (
        "generateButton",
        "copyLuaCommandButton",
        "openOutputButton",
        "copyOutputButton",
    ):
        control = item(root, name)
        position = control.mapTo(root, QPoint(0, 0))
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
    QTest.keyClick(QApplication.focusWidget(), Qt.Key.Key_Escape)
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
        return tmp_path / "shutdown.lua"

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = str(tmp_path)
    controller.form.name = "Shutdown active worker"
    controller.generate()
    controller.shutdown()
    assert finished.is_set()
    shiboken6.delete(controller)


def test_tabs_move_with_their_pages_and_keyboard_navigation(window):
    root, controller = window
    root.tabs.setCurrentWidget(root.settings_page)
    bar = root.tabs.tabBar()
    assert root.tabs.count() == 3
    start = bar.tabRect(2).center()
    finish = bar.tabRect(0).center()
    QTest.mousePress(bar, Qt.MouseButton.LeftButton, pos=start)
    for x in range(start.x(), finish.x() - 1, -5):
        QTest.mouseMove(bar, QPoint(x, start.y()), delay=20)
    QTest.mouseRelease(bar, Qt.MouseButton.LeftButton, pos=finish)
    assert root.tabs.widget(0) is root.settings_page
    assert root.tabs.currentWidget() is root.settings_page
    assert root.tabs.tabText(0) == "&Settings"
    QTest.keyClick(root.tabs, Qt.Key.Key_Tab, Qt.KeyboardModifier.ControlModifier)
    assert root.tabs.currentWidget() is root.generate_page
    assert isinstance(root.settings_page.layout(), QFormLayout)
    assert root.styleSheet() == ""
    assert all(widget.styleSheet() == "" for widget in root.findChildren(QWidget))


def test_files_edit_and_picker_update_generation_destination(window, tmp_path, monkeypatch):
    root, controller = window
    root.tabs.setCurrentWidget(root.files_page)
    field = item(root, "saveDirectoryField")
    assert root.files_page.isAncestorOf(field)
    assert not root.settings_page.isAncestorOf(field)
    field.setFocus()
    field.selectAll()
    target = tmp_path / "chosen output"
    QTest.keyClicks(field, str(target))
    QTest.keyClick(field, Qt.Key.Key_Tab)
    assert controller.profile.save_directory == target
    selected = tmp_path / "selected folder"
    root.save_dialog.fileSelected.emit(str(selected))
    assert field.text() == str(selected)
    assert controller.form.snapshot(controller.profile.save_directory).output_directory == selected
    opened = []
    monkeypatch.setattr("drlua.ui.controller.QDesktopServices.openUrl", opened.append)
    controller.openOutput()
    assert selected.is_dir()
    assert opened[0].toLocalFile() == selected.as_posix()


def test_file_menu_actions_and_about_dialog(window, tmp_path):
    root, controller = window
    root.tabs.setCurrentWidget(root.settings_page)
    root.folder_dialog.filesSelected.emit([str(tmp_path)])
    assert root.tabs.currentWidget() is root.generate_page
    assert Path(controller.form.sources) == tmp_path
    help_menu = root.menuBar().actions()[1].menu()
    help_menu.actions()[0].trigger()
    assert root.about_dialog.isVisible()
    QTest.keyClick(root.about_dialog, Qt.Key.Key_Escape)
    assert not root.about_dialog.isVisible()


def test_files_tab_lists_only_lua_filenames_and_copies_selected_commands(window):
    root, controller = window
    directory = controller.profile.save_directory
    directory.mkdir()
    first = directory / "Alpha sample.lua"
    second = directory / "Beta.LUA"
    first.write_text("return 1")
    second.write_text("return 2")
    (directory / "notes.txt").write_text("not Lua")
    (directory / "folder.lua").mkdir()
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: root.files.count() == 2)
    assert [root.files.item(i).text() for i in range(2)] == [first.name, second.name]
    assert not root.copy_commands.isEnabled()
    root.files.item(1).setSelected(True)
    click(root, "copySelectedCommandsButton")
    assert QApplication.clipboard().text() == f"dofile([[{second.as_posix()}]])"
    assert root.files_status.text() == "Copied 1 command to clipboard."
    root.files.item(0).setSelected(True)
    click(root, "copySelectedCommandsButton")
    assert QApplication.clipboard().text() == (
        f"dofile([[{first.as_posix()}]])\ndofile([[{second.as_posix()}]])"
    )
    assert root.files_status.text() == "Copied 2 commands to clipboard."
    root.files.clearSelection()
    assert not root.copy_commands.isEnabled()


def test_files_tab_refreshes_directory_and_quotes_bracketed_paths(window, tmp_path):
    root, controller = window
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: not controller._jobs)
    assert root.files.count() == 0
    directory = tmp_path / "new saves"
    directory.mkdir()
    script = directory / "Clip ]] Ã©.lua"
    script.write_text("return 1")
    controller.saveDirectory = str(directory)
    wait_until(lambda: root.files.count() == 1)
    assert root.files.item(0).text() == script.name
    root.files.item(0).setSelected(True)
    click(root, "copySelectedCommandsButton")
    assert QApplication.clipboard().text() == f"dofile([=[{script.as_posix()}]=])"
    script.unlink()
    click(root, "refreshFilesButton")
    wait_until(lambda: not controller._jobs)
    assert root.files.count() == 0
    assert not root.copy_commands.isEnabled()
    assert root.files_status.text() == ""
    script.write_text("return 2")
    click(root, "refreshFilesButton")
    wait_until(lambda: root.files.count() == 1)
    assert root.files.item(0).text() == script.name
    root.save_directory.setFocus()
    root.files.item(0).setSelected(True)
    changed = QSignalSpy(controller.saveDirectoryChanged)
    click(root, "copySelectedCommandsButton")
    assert changed.count() == 0
    assert root.files.item(0).isSelected()
    script.unlink()
    root.tabs.setCurrentWidget(root.settings_page)
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: not controller._jobs)
    assert root.files.count() == 0


def test_files_copy_reports_clipboard_failure(window, monkeypatch):
    root, controller = window
    directory = controller.profile.save_directory
    directory.mkdir()
    (directory / "sample.lua").write_text("return 1")
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: root.files.count() == 1)
    root.files.item(0).setSelected(True)
    clipboard = QApplication.clipboard()
    clipboard.setText("previous clipboard contents")
    monkeypatch.setattr(clipboard, "setText", lambda text: None)
    click(root, "copySelectedCommandsButton")
    assert root.files_status.text() == "Failed to copy 1 command to clipboard."
    assert clipboard.text() == "previous clipboard contents"


@pytest.mark.parametrize("copied", [True, False])
def test_generated_command_copy_reports_clipboard_status(window, monkeypatch, tmp_path, copied):
    from unittest.mock import Mock

    root, controller = window
    controller.generationResult(tmp_path / "generated.lua")
    clipboard = Mock()
    clipboard.text.return_value = controller.generatedCommand if copied else "previous clipboard contents"
    monkeypatch.setattr(QGuiApplication, "clipboard", lambda: clipboard)
    click(root, "copyLuaCommandButton")
    clipboard.setText.assert_called_once_with(controller.generatedCommand)
    expected = "Copied 1 command to clipboard." if copied else "Failed to copy 1 command to clipboard."
    assert item(root, "statusLabel").text() == expected


def test_source_metadata_does_not_block_generate_feedback(window, monkeypatch, tmp_path):
    from drlua.ui import form as form_module

    root, controller = window
    entered = threading.Event()
    release = threading.Event()
    original = form_module.source_metadata
    received = []

    def slow_metadata(source):
        assert QThread.currentThread() != QApplication.instance().thread()
        entered.set()
        release.wait(5)
        return original(source)

    def generate(paths, **kwargs):
        received.append(paths)
        return kwargs["output_directory"] / "generated.lua"

    monkeypatch.setattr(form_module, "source_metadata", slow_metadata)
    monkeypatch.setattr(generation, "create_bins", generate)
    root.sources.setPlainText(str(tmp_path))
    root.sources.setFocus()
    click(root, "generateButton")
    wait_until(entered.is_set)
    assert controller.busy
    assert not root.generate_button.isEnabled()
    assert "Preparing source metadata" in root.status.text()
    assert "Starting generation" in root.output.toPlainText()
    assert root.progress.maximum() == 0
    QTest.qWait(150)
    assert controller.busy
    assert not received
    for _ in range(3):
        click(root, "generateButton")
    assert not received
    release.set()
    wait_until(lambda: not controller.busy)
    assert received == [[tmp_path]]


def test_worker_exception_is_visible_without_suppressing_it(window, monkeypatch, tmp_path):
    import sys

    root, controller = window
    exceptions = []

    def report(exception_type, exception, tb):
        exceptions.append(exception)
        controller.reportException(exception_type, exception, tb)

    monkeypatch.setattr(sys, "excepthook", report)
    controller.form.sources = str(tmp_path / "missing source")
    controller.form.name = "Failure regression"
    click(root, "generateButton")
    wait_until(lambda: bool(exceptions) and not controller.busy)
    assert isinstance(exceptions[0], RuntimeError)
    assert "Failed:" in root.status.text()
    assert "Could not process input location" in root.status.text()
    assert "Traceback" in root.output.toPlainText()
    assert "missing source" in root.output.toPlainText()
    assert not root.copy_lua.isEnabled()


def test_file_url_paste_preserves_hash_and_drive_separator(window, tmp_path):
    from PySide6.QtCore import QMimeData

    root, controller = window
    folder = tmp_path / "Folder #Tag"
    folder.mkdir()
    mime = QMimeData()
    mime.setUrls([QUrl.fromLocalFile(str(folder))])
    root.sources.insertFromMimeData(mime)
    assert Path(controller.form.sources) == folder
    assert "%23" not in controller.form.sources


def test_pending_generation_uses_requested_source_metadata(window, monkeypatch, tmp_path):
    from drlua.ui import form as form_module

    root, controller = window
    release = threading.Event()
    received = []
    source = tmp_path / "original"

    def metadata(path):
        release.wait(3)
        return path, "Original inferred name", ("Test section", "Test category")

    def generate(paths, **kwargs):
        received.append((paths, kwargs))
        return kwargs["output_directory"] / "original.lua"

    monkeypatch.setattr(form_module, "source_metadata", metadata)
    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.appendUrls([QUrl.fromLocalFile(str(source))])
    controller.form.tags = "explicit tag"
    click(root, "generateButton")
    controller.form.sources = str(tmp_path / "next run")
    controller.form.name = "Next name"
    controller.form.tags = "Next tags"
    release.set()
    wait_until(lambda: not controller.busy)
    assert received[0][0] == [source]
    assert received[0][1]["name"] == "Original inferred name"
    assert received[0][1]["tag"] == ["explicit tag"]


def test_pending_generation_survives_new_source_inference(window, monkeypatch, tmp_path):
    from drlua.ui import form as form_module

    root, controller = window
    original_source = tmp_path / "original"
    next_source = tmp_path / "next"
    release = threading.Event()
    received = []

    def metadata(source):
        if Path(source) == original_source:
            release.wait(3)
        return source, Path(source).name, ("Test section", "")

    def generate(paths, **kwargs):
        received.append((paths, kwargs["name"]))
        return kwargs["output_directory"] / "original.lua"

    monkeypatch.setattr(form_module, "source_metadata", metadata)
    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = str(original_source)
    click(root, "generateButton")
    controller.form.sources = str(next_source)
    controller.form.inferSource()
    wait_until(lambda: controller.form.name == "next")
    release.set()
    wait_until(lambda: not controller.busy)
    assert received == [([original_source], "original")]
    assert controller.form.name == "next"


def test_cancel_finished_metadata_before_queued_result_and_restart(window, monkeypatch, tmp_path):
    from drlua.ui import form as form_module

    root, controller = window
    release = threading.Event()
    sample = Path(__file__).resolve().parents[1] / "data" / "sample" / "h1.mp4"

    def metadata(source):
        release.wait(3)
        return source, "Discarded metadata", ("Test section", "")

    monkeypatch.setattr(form_module, "source_metadata", metadata)
    controller.form.sources = str(sample)
    click(root, "generateButton")
    job = controller._pending_job
    release.set()
    assert job.wait(3000)
    click(root, "cancelButton")
    assert not controller.busy
    assert not controller.canCancel
    controller.form.name = "Restart after cancellation"
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    assert controller.form.name == "Restart after cancellation"
    assert controller.generatedCommand
    assert len(list((tmp_path / "output").glob("*.lua"))) == 1


def test_stale_generation_signals_do_not_change_current_run(window, monkeypatch, tmp_path):
    from drlua.ui.jobs import GenerationJob

    root, controller = window
    release = threading.Event()
    entered = threading.Event()

    def generate(paths, **kwargs):
        entered.set()
        release.wait(3)
        return kwargs["output_directory"] / "current.lua"

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = str(tmp_path)
    controller.form.name = "Current run"
    old = GenerationJob(controller.form.snapshot(tmp_path), controller)
    old.progress.connect(controller.receiveProgress)
    old.activity.connect(controller.receiveActivity)
    old.resultReady.connect(controller.generationResult)
    old.finished.connect(controller.generationFinished)
    click(root, "generateButton")
    wait_until(entered.is_set)
    active = controller._active_job
    status = controller.status
    old.progress.emit("Complete", 1, 1, time.perf_counter())
    old.activity.emit("Stale activity")
    old.resultReady.emit(tmp_path / "stale.lua")
    old.finished.emit()
    assert controller._active_job is active
    assert controller.busy
    assert controller.status == status
    assert not controller.generatedCommand
    release.set()
    wait_until(lambda: not controller.busy)
    assert "current.lua" in controller.generatedCommand


def test_unrelated_exception_does_not_unlock_running_generate(window, monkeypatch, tmp_path):
    root, controller = window
    entered = threading.Event()
    release = threading.Event()

    def generate(paths, **kwargs):
        entered.set()
        release.wait(3)
        return kwargs["output_directory"] / "generated.lua"

    monkeypatch.setattr(generation, "create_bins", generate)
    controller.form.sources = str(tmp_path)
    controller.form.name = "Busy regression"
    click(root, "generateButton")
    wait_until(entered.is_set)
    controller.reportException(RuntimeError, RuntimeError("unrelated operation"), None)
    QTest.qWait(50)
    still_busy = controller.busy
    enabled = root.generate_button.isEnabled()
    release.set()
    wait_until(lambda: not controller.busy)
    assert still_busy
    assert not enabled


def test_metadata_failure_does_not_leave_next_run_waiting(window, monkeypatch, tmp_path):
    import sys
    from drlua.ui import form as form_module

    root, controller = window
    exceptions = []
    original = form_module.source_metadata

    def fail_metadata(source):
        raise OSError("metadata unavailable")

    def report(kind, exception, tb):
        exceptions.append(exception)
        controller.reportException(kind, exception, tb)

    monkeypatch.setattr(sys, "excepthook", report)
    monkeypatch.setattr(form_module, "source_metadata", fail_metadata)
    controller.form.sources = str(tmp_path)
    click(root, "generateButton")
    wait_until(lambda: bool(exceptions) and not controller.busy and not controller.form._jobs)
    assert "metadata unavailable" in root.output.toPlainText()
    assert not controller.form.inferencePending
    monkeypatch.setattr(form_module, "source_metadata", original)
    received = []

    def generate(paths, **kwargs):
        received.append(kwargs["name"])
        return kwargs["output_directory"] / "next.lua"

    monkeypatch.setattr(generation, "create_bins", generate)
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    assert received == [tmp_path.name]


def test_cleared_name_is_inferred_again_for_same_source(window, monkeypatch, tmp_path):
    root, controller = window
    controller.form.appendUrls([QUrl.fromLocalFile(str(tmp_path))])
    wait_until(lambda: not controller.form.inferencePending)
    controller.form.name = ""
    received = []

    def generate(paths, **kwargs):
        received.append(kwargs["name"])
        return kwargs["output_directory"] / "named.lua"

    monkeypatch.setattr(generation, "create_bins", generate)
    click(root, "generateButton")
    wait_until(lambda: not controller.busy)
    assert received == [tmp_path.name]


def test_files_context_menu_copy_and_delete(window, monkeypatch):
    from PySide6.QtGui import QContextMenuEvent
    from PySide6.QtWidgets import QMessageBox

    root, controller = window
    directory = controller.profile.save_directory
    directory.mkdir()
    first = directory / "first.lua"
    second = directory / "second.lua"
    first.write_text("return 1")
    second.write_text("return 2")
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: root.files.count() == 2)
    root.files.setCurrentRow(0)
    target = root.files.item(1)
    point = root.files.visualItemRect(target).center()
    QApplication.sendEvent(root.files.viewport(), QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, point, root.files.viewport().mapToGlobal(point)
    ))
    menu = root.files.context_menu
    assert menu.isVisible()
    assert root.files.selectedItems() == [target]
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton,
                     pos=menu.actionGeometry(root.copy_file_action).center())
    assert QApplication.clipboard().text() == f"dofile([[{second.as_posix()}]])"
    root.files.setFocus()
    QApplication.sendEvent(root.files, QContextMenuEvent(
        QContextMenuEvent.Reason.Keyboard, QPoint(), root.files.mapToGlobal(QPoint())
    ))
    assert menu.isVisible()
    QTest.keyClick(menu, Qt.Key.Key_Down)
    QTest.keyClick(menu, Qt.Key.Key_Down)
    QTest.keyClick(menu, Qt.Key.Key_Down)
    QTest.keyClick(menu, Qt.Key.Key_Return)
    assert root.delete_prompt.isVisible()
    assert root.delete_prompt.defaultButton() == root.delete_prompt.button(QMessageBox.StandardButton.Cancel)
    QTest.keyClick(root.delete_prompt, Qt.Key.Key_Escape)
    assert second.exists()
    threads = []
    unlink = Path.unlink

    def remove(path):
        threads.append(QThread.currentThread())
        unlink(path)

    monkeypatch.setattr(Path, "unlink", remove)
    root.files.setFocus()
    QTest.keyClick(root.files, Qt.Key.Key_Delete)
    assert root.delete_prompt.isVisible()
    delete = next(button for button in root.delete_prompt.buttons()
                  if root.delete_prompt.buttonRole(button) == QMessageBox.ButtonRole.DestructiveRole)
    QTest.mouseClick(delete, Qt.MouseButton.LeftButton)
    wait_until(lambda: root.files.count() == 1 and not controller._jobs)
    assert not second.exists()
    assert first.exists()
    assert root.files.item(0).text() == first.name
    assert threads and all(thread != QApplication.instance().thread() for thread in threads)
    assert root.files_status.text() == "Deleted 1 saved Lua file(s)."


def test_files_rename_dialog_save_and_cancel(window, monkeypatch):
    from PySide6.QtGui import QContextMenuEvent
    from PySide6.QtWidgets import QDialogButtonBox

    root, controller = window
    directory = controller.profile.save_directory
    directory.mkdir()
    original = directory / "original.lua"
    original.write_text("return 42")
    root.tabs.setCurrentWidget(root.files_page)
    wait_until(lambda: root.files.count() == 1)
    assert not root.rename_file_action.isEnabled()
    point = root.files.visualItemRect(root.files.item(0)).center()
    QApplication.sendEvent(root.files.viewport(), QContextMenuEvent(
        QContextMenuEvent.Reason.Mouse, point, root.files.viewport().mapToGlobal(point)
    ))
    menu = root.files.context_menu
    QTest.mouseClick(menu, Qt.MouseButton.LeftButton,
                     pos=menu.actionGeometry(root.rename_file_action).center())
    assert root.rename_dialog.isVisible()
    filename = item(root.rename_dialog, "renameFilenameField")
    assert filename.text() == "original.lua"
    assert filename.selectedText() == "original"
    filename.setText("cancelled.lua")
    buttons = root.rename_dialog.findChild(QDialogButtonBox)
    QTest.mouseClick(buttons.button(QDialogButtonBox.StandardButton.Cancel), Qt.MouseButton.LeftButton)
    assert original.exists()
    assert not (directory / "cancelled.lua").exists()
    root.files.setFocus()
    QTest.keyClick(root.files, Qt.Key.Key_F2)
    assert root.rename_dialog.isVisible()
    filename = item(root.rename_dialog, "renameFilenameField")
    assert filename.text() == "original.lua"
    filename.setText("renamed.lua")
    threads = []
    rename = Path.rename

    def rename_on_disk(path, target):
        threads.append(QThread.currentThread())
        return rename(path, target)

    monkeypatch.setattr(Path, "rename", rename_on_disk)
    buttons = root.rename_dialog.findChild(QDialogButtonBox)
    QTest.mouseClick(buttons.button(QDialogButtonBox.StandardButton.Save), Qt.MouseButton.LeftButton)
    wait_until(lambda: not controller._jobs and root.files.count() == 1
               and root.files.item(0).text() == "renamed.lua")
    assert not original.exists()
    assert (directory / "renamed.lua").read_text() == "return 42"
    assert root.files.item(0).data(Qt.ItemDataRole.UserRole) == (directory / "renamed.lua").as_posix()
    assert threads and all(thread != QApplication.instance().thread() for thread in threads)
    assert root.files_status.text() == "Renamed file to renamed.lua."

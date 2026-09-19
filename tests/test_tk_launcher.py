from pathlib import Path
import time
import tkinter as tk

import pytest

from loguru import logger

from drlua.ui import application


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    yield root
    root.destroy()


@pytest.fixture
def launcher(monkeypatch, tmp_path, tk_root):
    monkeypatch.setattr(application, "SECTION_CATEGORY_DATA", {
        "Sections": {"Test section": {
            "Path": str(tmp_path),
            "Categories": {"Test category": {
                "Path": str(tmp_path / "category"), "Tags": ["first", "second"],
            }},
        }},
    })
    log_path = tmp_path / "drlua.log"
    sink = logger.add(log_path, format="{message}", catch=False)
    monkeypatch.setattr(application, "LOG_PATH", log_path)
    root = tk_root
    root.geometry("920x780")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    view = application.ApplicationView(root)
    view.grid(row=0, column=0, sticky="nsew")
    root.update()
    yield root, view
    view.destroy()
    logger.remove(sink)


def test_source_pickers_and_category_tags(launcher, monkeypatch, tmp_path):
    root, view = launcher
    folder = tmp_path / "category"
    folder.mkdir()
    monkeypatch.setattr(application.filedialog, "askdirectory", lambda **_: str(folder))
    monkeypatch.setattr(application.filedialog, "askopenfilenames", lambda **_: (str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")))
    assert view.send.instate(["disabled"])
    view.add_folder()
    view.add_files()
    root.update()
    assert view.source_paths() == [str(folder), str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")]
    assert view.name.get() == "category"
    assert view.section.get() == "Test section"
    assert view.category.get() == "Test category"
    assert view.tags.get("1.0", "end-1c") == "first\nsecond"
    assert view.send.instate(["!disabled"])
    view.category.set("Custom")
    assert view.tags.get("1.0", "end-1c") == "Custom"


def test_generation_uses_form_values_and_reenables_button(launcher, monkeypatch, tmp_path):
    root, view = launcher
    calls = []

    def generate(paths, **kwargs):
        calls.append((paths, kwargs))
        kwargs["progress"]("Probing media", 0, len(paths))
        logger.info("dofile([[generated.lua]])")
        kwargs["progress"]("Probing media", len(paths), len(paths))
        kwargs["progress"]("Complete", len(paths), len(paths))

    monkeypatch.setattr(application, "create_bins", generate)
    view.append_sources([str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")])
    view.name.set("My release")
    view.group.set("My group")
    view.tags.delete("1.0", "end")
    view.tags.insert("1.0", "alpha, beta\ngamma")
    view.send.invoke()
    assert view.busy
    assert view.send.instate(["disabled"])
    assert view.check_updates.instate(["disabled"])
    deadline = time.monotonic() + 5
    while view.busy and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert not view.busy
    assert view.check_updates.instate(["!disabled"])
    assert view.send.instate(["!disabled"])
    assert "Lua script created: 2/2 items" in view.status.get()
    assert float(view.progress["value"]) == float(view.progress["maximum"])
    assert calls[0][0] == [tmp_path / "one.mp4", tmp_path / "two.mp4"]
    assert calls[0][1]["name"] == "My release"
    assert calls[0][1]["group_name"] == "My group"
    assert calls[0][1]["tag"] == ["alpha", "beta", "gamma"]
    assert "dofile([[generated.lua]])" in view.output.get("1.0", "end")
    assert "\x1b" not in view.output.get("1.0", "end")
    assert view.output.cget("state") == "disabled"
    view.copy_output()
    assert "dofile([[generated.lua]])" in root.clipboard_get()


def test_resize_and_keyboard_focus(launcher):
    root, view = launcher
    root.geometry("700x660")
    root.update()
    small = view.output.winfo_width()
    assert view.send.winfo_rooty() > view.output.master.winfo_rooty() + view.output.master.winfo_height()
    status_label = view.grid_slaves(row=3, column=0)[0]
    assert status_label.winfo_rooty() > view.send.winfo_rooty() + view.send.winfo_height()
    assert view.send.winfo_rooty() + view.send.winfo_height() < root.winfo_rooty() + root.winfo_height()
    root.geometry("1200x900")
    root.update()
    assert view.output.winfo_width() > small
    view.name_entry.focus_force()
    view.name_entry.event_generate("<Tab>")
    root.update()
    assert root.focus_get() == view.sections


def test_form_generates_real_lua(tmp_path, monkeypatch):
    from drlua import create_bins

    monkeypatch.setattr(create_bins, "PROCESSED_DATA_DIR", tmp_path)
    sample = Path(__file__).resolve().parents[1] / "data" / "sample"
    log_path = tmp_path / "generation.log"
    sink = logger.add(log_path, catch=False)
    application._run_create_bins_from_form([str(sample)], "Tk sample", "Fansites", "", ["tk-test"])
    logger.remove(sink)
    assert "dofile([[" in log_path.read_text(encoding="utf-8")
    assert len(list((tmp_path / "create_bins").glob("*.lua"))) == 1


def test_output_tails_new_log_content_once(launcher):
    root, view = launcher
    logger.info("First update")
    view.refresh_output()
    assert "First update" in view.output.get("1.0", "end")
    logger.info("Second update")
    view.refresh_output()
    view.refresh_output()
    output = view.output.get("1.0", "end")
    assert output.count("First update") == 1
    assert output.count("Second update") == 1


def test_generation_failure_surfaces(monkeypatch, tmp_path):
    def generate(*args, **kwargs):
        raise RuntimeError("generation failed")

    monkeypatch.setattr(application, "create_bins", generate)
    with pytest.raises(RuntimeError, match="generation failed"):
        application._run_create_bins_from_form([str(tmp_path)], "Test", "Test", "", [])


def test_update_declined_keeps_form_and_reenables_actions(launcher, monkeypatch, tmp_path):
    root, view = launcher
    view.append_sources([str(tmp_path)])
    monkeypatch.setattr(application, "latest_release", lambda: {"tag_name": "v99.0.0"})
    monkeypatch.setattr(application.messagebox, "askyesno", lambda *args, **kwargs: False)
    view.check_updates.invoke()
    assert view.send.instate(["disabled"])
    deadline = time.monotonic() + 5
    while view.busy and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert not view.busy
    assert view.source_paths() == [str(tmp_path)]
    assert view.send.instate(["!disabled"])
    assert view.check_updates.instate(["!disabled"])


def test_update_download_closes_app_before_launch(monkeypatch, tmp_path):
    import ctypes
    from ctypes import wintypes
    from types import SimpleNamespace
    from unittest.mock import Mock

    setup = tmp_path / "DrLua-99.0.0-windows-amd64-Setup.exe"
    events = []
    root = Mock()
    mutex_name = f"DrLua.Test.{tmp_path.name}"
    create_mutex = ctypes.windll.kernel32.CreateMutexW
    create_mutex.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.LPCWSTR]
    create_mutex.restype = wintypes.HANDLE

    def create_test_mutex(attributes, owner, name):
        assert name == "electblake.DrLua.Running"
        return create_mutex(attributes, owner, mutex_name)

    monkeypatch.setattr(ctypes.windll.kernel32, "CreateMutexW", create_test_mutex)
    open_mutex = ctypes.windll.kernel32.OpenMutexW
    open_mutex.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
    open_mutex.restype = wintypes.HANDLE

    def mainloop():
        handle = open_mutex(0x00100000, False, mutex_name)
        assert handle
        close_handle = ctypes.windll.kernel32.CloseHandle
        close_handle.argtypes = [wintypes.HANDLE]
        close_handle(handle)
        events.append("closed")

    root.mainloop.side_effect = mainloop
    executor = Mock()
    executor.shutdown.side_effect = lambda **kwargs: events.append("workers finished")
    view = SimpleNamespace(executor=executor, setup_path=setup, grid=Mock())

    def launch(path):
        assert not open_mutex(0x00100000, False, mutex_name)
        assert path == setup
        assert events == ["closed", "workers finished"]
        events.append("launched")

    monkeypatch.setattr(application.tk, "Tk", lambda: root)
    monkeypatch.setattr(application, "ApplicationView", lambda *args: view)
    monkeypatch.setattr(application.os, "startfile", launch)
    assert application.run_application() == 0
    assert events == ["closed", "workers finished", "launched"]


def test_accepted_update_downloads_before_closing(launcher, monkeypatch, tmp_path):
    from types import SimpleNamespace

    root, view = launcher
    setup = tmp_path / "DrLua-99.0.0-windows-amd64-Setup.exe"
    release = {"tag_name": "v99.0.0"}
    events = []
    monkeypatch.setattr(application, "latest_release", lambda: release)
    monkeypatch.setattr(application.messagebox, "askyesno", lambda *args, **kwargs: True)

    def download(selected):
        assert selected == release
        events.append("downloaded")
        return setup

    monkeypatch.setattr(application, "download_setup", download)
    monkeypatch.setattr(view, "winfo_toplevel", lambda: SimpleNamespace(destroy=lambda: events.append("closed")))
    view.check_updates.invoke()
    deadline = time.monotonic() + 5
    while "closed" not in events and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert events == ["downloaded", "closed"]
    assert view.setup_path == setup
    assert view.update_poll_id is None


def test_current_release_keeps_app_open(launcher, monkeypatch):
    root, view = launcher
    monkeypatch.setattr(application, "latest_release", lambda: {"tag_name": f"v{application.__version__}"})
    view.check_updates.invoke()
    deadline = time.monotonic() + 5
    while view.busy and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert not view.busy
    assert "up to date" in view.status.get()
    assert view.setup_path is None
    assert view.check_updates.instate(["!disabled"])


def test_progress_counts_rate_eta_and_finalization(launcher, monkeypatch):
    from queue import SimpleQueue

    root, view = launcher
    view.progress_events = SimpleQueue()
    view.progress_stage = "Scanning sources"
    view.progress_events.put(("Probing media", 0, 10, 100.0))
    view.refresh_progress()
    assert "ETA —" in view.status.get()
    view.progress_events.put(("Probing media", 4, 10, 102.0))
    monkeypatch.setattr(application.time, "perf_counter", lambda: 102.0)
    view.refresh_progress()
    assert float(view.progress["value"]) == 4
    assert float(view.progress["maximum"]) == 12
    assert "4/10 items" in view.status.get()
    assert "2.00 items/s" in view.status.get()
    assert "ETA 0:03" in view.status.get()

    # Recompute while the next probe is still running, without a new event.
    monkeypatch.setattr(application.time, "perf_counter", lambda: 104.0)
    view.refresh_progress()
    assert "1.00 items/s" in view.status.get()
    assert "ETA 0:06" in view.status.get()
    view.progress_events.put(("Probing media", 10, 10, 105.0))
    view.progress_events.put(("Grouping clips", 10, 10, 105.1))
    view.refresh_progress()
    assert "Grouping clips" in view.status.get()
    assert "ETA finalizing" in view.status.get()
    assert float(view.progress["value"]) < float(view.progress["maximum"])
    view.progress_events.put(("Writing Lua script", 10, 10, 105.2))
    view.refresh_progress()
    assert "Writing Lua script" in view.status.get()
    assert float(view.progress["value"]) == 11
    view.progress_events.put(("Complete", 10, 10, 105.3))
    view.refresh_progress()
    assert float(view.progress["value"]) == float(view.progress["maximum"])
    assert "Lua script created: 10/10 items" in view.status.get()
    assert "2.00 items/s" in view.status.get()
    assert "ETA 0:00" in view.status.get()

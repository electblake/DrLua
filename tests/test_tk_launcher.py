from pathlib import Path
import time
import tkinter as tk

import pytest

from drlua.ui import interactive


@pytest.fixture(scope="module")
def tk_root():
    root = tk.Tk()
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    yield root
    root.destroy()


@pytest.fixture
def launcher(monkeypatch, tmp_path, tk_root):
    monkeypatch.setattr(interactive, "SECTION_CATEGORY_DATA", {
        "Sections": {"Test section": {
            "Path": str(tmp_path),
            "Categories": {"Test category": {
                "Path": str(tmp_path / "category"), "Tags": ["first", "second"],
            }},
        }},
    })
    root = tk_root
    root.geometry("920x780")
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)
    view = interactive.LauncherView(root)
    view.grid(row=0, column=0, sticky="nsew")
    root.update()
    yield root, view
    view.destroy()


def test_source_pickers_and_category_tags(launcher, monkeypatch, tmp_path):
    root, view = launcher
    folder = tmp_path / "category"
    folder.mkdir()
    monkeypatch.setattr(interactive.filedialog, "askdirectory", lambda **_: str(folder))
    monkeypatch.setattr(interactive.filedialog, "askopenfilenames", lambda **_: (str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")))
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
        print("\x1b[32mdofile([[generated.lua]])\x1b[0m")

    monkeypatch.setattr(interactive, "create_bins", generate)
    view.append_sources([str(tmp_path / "one.mp4"), str(tmp_path / "two.mp4")])
    view.name.set("My release")
    view.group.set("My group")
    view.tags.delete("1.0", "end")
    view.tags.insert("1.0", "alpha, beta\ngamma")
    view.send.invoke()
    assert view.busy
    assert view.send.instate(["disabled"])
    deadline = time.monotonic() + 5
    while view.busy and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert not view.busy
    assert view.send.instate(["!disabled"])
    assert calls[0][0] == [tmp_path / "one.mp4", tmp_path / "two.mp4"]
    assert calls[0][1]["name"] == "My release"
    assert calls[0][1]["group_name"] == "My group"
    assert calls[0][1]["tag"] == ["alpha", "beta", "gamma"]
    assert calls[0][1]["prompt_for_missing_tags"] is False
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
    result, output = interactive._run_create_bins_from_form([str(sample)], "Tk sample", "Fansites", "", ["tk-test"])
    assert result == 0
    assert "dofile([[" in output
    assert len(list((tmp_path / "create_bins").glob("*.lua"))) == 1

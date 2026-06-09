from __future__ import annotations

import os
import re
import subprocess
import threading

from pathlib import Path

import pyperclip
import typer

from textual.app import App, ComposeResult
from textual.widgets import SelectionList

from drlua.config import PROCESSED_DATA_DIR
from drlua.helpers import luautil


copy_app = typer.Typer()

DATE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}(?:-\d{6})?")


def _copy_with_pyperclip_timeout(text: str, timeout_seconds: float = 1.5) -> bool:
    error: list[BaseException] = []

    def _worker() -> None:
        try:
            pyperclip.copy(text)
        except BaseException as exc:  # pragma: no cover - defensive thread boundary
            error.append(exc)

    thread = threading.Thread(target=_worker, daemon=True)
    thread.start()
    thread.join(timeout_seconds)
    if thread.is_alive():
        return False
    if error:
        raise error[0]
    return True


def _copy_to_clipboard(text: str) -> bool:
    if os.name == "nt":
        try:
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            subprocess.run(
                ["clip"],
                input=text,
                text=True,
                check=True,
                timeout=2,
                creationflags=creationflags,
            )
            return True
        except Exception:
            pass

    try:
        return _copy_with_pyperclip_timeout(text)
    except Exception:
        return False


def _extract_leading_name(file_path: Path) -> str:
    stem = file_path.stem
    match = DATE_PATTERN.search(stem)
    if not match:
        return stem
    candidate = stem[: match.start()].rstrip("._- ")
    return candidate or stem


def _find_processed_lua_files() -> list[Path]:
    lua_files = [
        path
        for path in PROCESSED_DATA_DIR.rglob("*.lua")
        if "done" not in {part.casefold() for part in path.relative_to(PROCESSED_DATA_DIR).parts}
    ]
    return sorted(lua_files, key=lambda path: path.name.casefold())


class LuaSelectionApp(App[list[Path] | None]):
    BINDINGS = [
        ("enter", "confirm", "Confirm"),
        ("escape", "cancel", "Cancel"),
        ("q", "cancel", "Cancel"),
    ]

    def __init__(self, files: list[Path]) -> None:
        super().__init__()
        self.files = files

    def compose(self) -> ComposeResult:
        selections: list[tuple[str, str, bool]] = []
        for index, file_path in enumerate(self.files, start=1):
            leading_name = _extract_leading_name(file_path)
            label = f"{index}. {file_path.name}"
            if leading_name != file_path.stem:
                label = f"{label}  [{leading_name}]"
            selections.append((label, str(file_path), False))

        yield LuaSelectionList(*selections)

    def action_confirm(self) -> None:
        widget = self.query_one(SelectionList[str])
        selected = [Path(path) for path in widget.selected]
        self.exit(result=selected)

    def action_cancel(self) -> None:
        self.exit(result=None)


class LuaSelectionList(SelectionList[str]):
    BINDINGS = [
        ("space", "select", "Toggle"),
        ("enter", "app.confirm", "Confirm"),
        ("escape", "app.cancel", "Cancel"),
        ("q", "app.cancel", "Cancel"),
    ]


@copy_app.command("copy")
def copy_command(
    name: str | None = typer.Option(None, "--name", help="Optional name/tag filter before the date in processed Lua filenames."),
) -> None:
    query: str | None = None
    if name is not None:
        query = name.strip().casefold()
        if not query:
            raise RuntimeError("Name cannot be empty")

    matches = _find_processed_lua_files()
    if query is not None:
        matches = [path for path in matches if query in _extract_leading_name(path).casefold()]

    if not matches:
        raise RuntimeError(f"No available Lua files found under processed data: {PROCESSED_DATA_DIR}")

    selected_files = LuaSelectionApp(matches).run()
    if not selected_files:
        typer.echo("No file selected.")
        return

    dofile_commands = [luautil.lua_dofile_command(file_path).strip() for file_path in selected_files]
    clipboard_text = "\n".join(dofile_commands)
    if not _copy_to_clipboard(clipboard_text):
        raise RuntimeError("Clipboard copy failed")

    typer.echo(f"Copied {len(dofile_commands)} dofile command(s) to clipboard:")
    for command in dofile_commands:
        typer.echo(command)

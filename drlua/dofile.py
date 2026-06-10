from __future__ import annotations

import re

from pathlib import Path

from iterfzf import iterfzf

import pyperclip
import typer

from drlua.config import DATA_DIR

dofile_app = typer.Typer()

DATE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}(?:-\d{6})?")


def _extract_leading_name(file_path: Path) -> str:
    stem = file_path.stem
    match = DATE_PATTERN.search(stem)
    if not match:
        return stem
    candidate = stem[: match.start()].rstrip("._- ")
    return candidate or stem


def _find_data_subdirs() -> list[Path]:
    subdirs = [path for path in DATA_DIR.iterdir() if path.is_dir()]
    return sorted(subdirs, key=lambda path: path.name.casefold())


def _find_lua_files(root_dir: Path) -> list[Path]:
    lua_files = [
        path
        for path in root_dir.rglob("*.lua")
        if "done" not in {part.casefold() for part in path.relative_to(root_dir).parts}
    ]
    return sorted(lua_files, key=lambda path: path.name.casefold())


def _choose_directory(directories: list[Path]) -> Path | None:
    labels = [directory.name for directory in directories]
    directory_by_label = dict(zip(labels, directories, strict=True))
    try:
        selected = iterfzf(
            labels,
            prompt="Data dir> ",
            header=f"Select a subdirectory from {DATA_DIR}",
            cycle=True,
        )
    except KeyboardInterrupt:
        return None
    if selected is None:
        return None
    return directory_by_label[selected]


def _format_file_label(root_dir: Path, file_path: Path) -> str:
    relative_path = file_path.relative_to(root_dir).as_posix()
    leading_name = _extract_leading_name(file_path)
    if leading_name != file_path.stem:
        return f"{file_path.name}\t{relative_path}\t[{leading_name}]"
    return f"{file_path.name}\t{relative_path}"


def _choose_files(root_dir: Path, files: list[Path], query: str | None) -> list[Path] | None:
    labels = [_format_file_label(root_dir, file_path) for file_path in files]
    file_by_label = dict(zip(labels, files, strict=True))
    try:
        selected = iterfzf(
            labels,
            multi=True,
            prompt=f"{root_dir.name}> ",
            header="Tab marks files. Enter confirms.",
            query=query or "",
            cycle=True,
        )
    except KeyboardInterrupt:
        return None
    if not selected:
        return None
    return [file_by_label[label] for label in selected]


@dofile_app.command("dofile")
def dofile_command(
    name: str | None = typer.Option(None, "--name", help="Optional initial filter for Lua filenames."),
) -> None:
    query: str | None = None
    if name is not None:
        query = name.strip()
        if not query:
            raise RuntimeError("Name cannot be empty")

    directories = _find_data_subdirs()
    if not directories:
        raise RuntimeError(f"No subdirectories found under data dir: {DATA_DIR}")

    selected_dir = _choose_directory(directories)
    if selected_dir is None:
        typer.echo("No directory selected.")
        return

    matches = _find_lua_files(selected_dir)
    if not matches:
        raise RuntimeError(f"No available Lua files found under selected directory: {selected_dir}")

    selected_files = _choose_files(selected_dir, matches, query)
    if not selected_files:
        typer.echo("No file selected.")
        return

    dofile_commands = [f"dofile([[{file_path.as_posix()}]])" for file_path in selected_files]
    clipboard_text = "\n".join(dofile_commands)
    pyperclip.copy(clipboard_text)

    typer.echo(f"Copied {len(dofile_commands)} dofile command(s) to clipboard:")
    for command in dofile_commands:
        typer.echo(command)

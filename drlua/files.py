from __future__ import annotations

import json
import re
import shutil
from datetime import datetime

from pathlib import Path

from iterfzf import iterfzf

from drlua.config import DATA_DIR
from drlua.helpers.scene_release import parse_scene_release, scene_release_to_string

DATE_PATTERN = re.compile(r"\d{4}\.\d{2}\.\d{2}(?:-\d{6})?")
RELEASE_NAME_PATTERNS = (
    re.compile(r'(?m)^[ \t]*(?:\[\s*["\']release_name["\']\s*\]|release_name)\s*=\s*"([^"\r\n]+)"'),
)
SOURCE_PATH_PATTERNS = (
    re.compile(r"(?m)^-- Source folder:\s*(.+)$"),
    re.compile(r'(?m)^[ \t]*(?:\[\s*["\']source_folder["\']\s*\]|SOURCE_FOLDER)\s*=\s*"([^"\r\n]+)"'),
    re.compile(r'(?m)^[ \t]*(?:\[\s*["\']path["\']\s*\]|path)\s*=\s*"([^"\r\n]+)"'),
)


def _resolve_fzf_executable() -> str | None:
    return shutil.which("fzf.exe") or shutil.which("fzf")


def _iterfzf_select(
    labels: list[str],
    *,
    prompt: str,
    header: str,
    multi: bool = False,
    query: str = "",
) -> str | list[str] | None:
    fzf_executable = _resolve_fzf_executable()
    if fzf_executable:
        try:
            return iterfzf(
                labels,
                multi=multi,
                prompt=prompt,
                header=header,
                query=query,
                cycle=True,
                executable=fzf_executable,
                __extra__=("--layout=default",),
            )
        except FileNotFoundError:
            pass
        except KeyboardInterrupt:
            return None

    print(header)
    for index, label in enumerate(labels, start=1):
        print(f"{index}. {label}")

    if multi:
        response = input("Select number(s), comma-separated: ").strip()
        if not response.strip():
            return None
        selected_labels: list[str] = []
        for raw_index in response.split(","):
            value = raw_index.strip()
            if not value:
                continue
            index = int(value)
            if index < 1 or index > len(labels):
                raise RuntimeError(f"Selection out of range: {value}")
            selected_labels.append(labels[index - 1])
        return selected_labels

    response = input("Select number: ").strip()
    if not response.strip():
        return None
    index = int(response.strip())
    if index < 1 or index > len(labels):
        raise RuntimeError(f"Selection out of range: {response}")
    return labels[index - 1]


def _select_data_directory() -> Path | None:
    directories = sorted((path for path in DATA_DIR.iterdir() if path.is_dir()), key=lambda path: path.name.casefold())
    if not directories:
        raise RuntimeError(f"No subdirectories found under data dir: {DATA_DIR}")

    directory_labels: list[str] = []
    directory_by_label: dict[str, Path] = {}
    for directory in directories:
        label = f"{directory.name} ({sum(1 for path in directory.glob('**/*.lua') if path.is_file())})"
        directory_labels.append(label)
        directory_by_label[label] = directory

    try:
        selected_directory = _iterfzf_select(
            directory_labels,
            prompt="Data dir> ",
            header=f"Select a subdirectory from {DATA_DIR}",
        )
    except KeyboardInterrupt:
        selected_directory = None

    if not isinstance(selected_directory, str):
        return None
    return directory_by_label[selected_directory]


def _available_lua_files(selected_dir: Path) -> tuple[list[str], dict[str, Path]]:
    matches = [
        path
        for path in selected_dir.rglob("*.lua")
        if "done" not in {part.casefold() for part in path.relative_to(selected_dir).parts}
    ]
    if not matches:
        raise RuntimeError(f"No available Lua files found under selected directory: {selected_dir}")

    matches.sort(
        key=lambda path: _lua_file_date(path) or datetime.min,
        reverse=True,
    )

    file_labels: list[str] = []
    file_by_label: dict[str, Path] = {}
    for file_path in matches:
        relative_path = file_path.relative_to(selected_dir).as_posix()
        stem = file_path.stem
        match = DATE_PATTERN.search(stem)
        leading_name = stem
        if match:
            candidate = stem[: match.start()].rstrip("._- ")
            if candidate:
                leading_name = candidate
        label = f"{file_path.name}\t{relative_path}"
        if leading_name != stem:
            label = f"{label}\t[{leading_name}]"
        file_labels.append(label)
        file_by_label[label] = file_path
    return file_labels, file_by_label


def _lua_file_date(file_path: Path) -> datetime | None:
    match = DATE_PATTERN.search(file_path.stem)
    if not match:
        return None
    date_text = match.group(0)
    if "-" in date_text:
        try:
            return datetime.strptime(date_text, "%Y.%m.%d-%H%M%S")
        except ValueError:
            return None
    try:
        return datetime.strptime(date_text, "%Y.%m.%d")
    except ValueError:
        return None


def _select_files(file_labels: list[str], selected_dir: Path, query: str) -> list[str]:
    try:
        selected_files = _iterfzf_select(
            file_labels,
            prompt=f"{selected_dir.name}> ",
            header="Tab marks files. Enter confirms.",
            multi=True,
            query=query,
        )
    except KeyboardInterrupt:
        selected_files = None

    selected_labels: list[str] = []
    if isinstance(selected_files, str):
        selected_labels.append(selected_files)
    elif isinstance(selected_files, (list, tuple)):
        for item in selected_files:
            if not isinstance(item, str):
                return []
            selected_labels.append(item)
    return selected_labels


def _select_action(selected_files: list[Path]) -> str | None:
    actions = [
        ("dofile", "Print dofile command(s)"),
        ("info", "Show release name and source path"),
        ("delete", "Delete the selected file(s)"),
    ]
    action_labels = [f"{name}\t{description}" for name, description in actions]
    action_by_label = {f"{name}\t{description}": name for name, description in actions}

    try:
        selected_action = _iterfzf_select(
            action_labels,
            prompt="Action> ",
            header=f"Choose action for {len(selected_files)} selected file(s)",
        )
    except KeyboardInterrupt:
        selected_action = None

    if not isinstance(selected_action, str):
        return None
    return action_by_label[selected_action]


def _clean_lua_string(value: str) -> str:
    return value.replace("\\\\", "\\")


def _find_first_string_match(lua_text: str, patterns: tuple[re.Pattern[str], ...]) -> str | None:
    for pattern in patterns:
        match = pattern.search(lua_text)
        if match:
            return _clean_lua_string(match.group(1).strip())
    return None


def _extract_file_info(lua_file: Path) -> dict[str, str]:
    lua_text = lua_file.read_text(encoding="utf-8")
    release_name = _find_first_string_match(lua_text, RELEASE_NAME_PATTERNS)
    source_path = _find_first_string_match(lua_text, SOURCE_PATH_PATTERNS)
    fallback_release_name = scene_release_to_string(parse_scene_release(lua_file.stem))

    return {
        "release_name": release_name or fallback_release_name or lua_file.stem or "<not found>",
        "source_path": source_path or "<not found>",
    }


def _print_dofile_commands(selected_files: list[Path]) -> None:
    dofile_commands = [f"dofile([[{file_path.as_posix()}]])" for file_path in selected_files]

    print(f"Dofile command(s) for {len(dofile_commands)} selected file(s):")
    for command in dofile_commands:
        print(command)


def _show_info(selected_files: list[Path]) -> None:
    for index, file_path in enumerate(selected_files):
        info = _extract_file_info(file_path)
        if index:
            print("")
        print(file_path.as_posix())
        print(json.dumps(info, indent=2, ensure_ascii=True))


def _delete_files(selected_files: list[Path]) -> None:
    file_count = len(selected_files)
    response = input(f"Delete {file_count} selected file(s)? [y/N]: ").strip().lower()
    confirmed = response in {"y", "yes"}
    if not confirmed:
        print("Delete cancelled.")
        return

    deleted_count = 0
    for file_path in selected_files:
        file_path.unlink(missing_ok=False)
        deleted_count += 1

    print(f"Deleted {deleted_count} file(s).")


def files_command(
    name: str | None = None,
) -> None:
    query = name.strip() if name is not None else ""
    if name is not None and not query:
        raise RuntimeError("Name cannot be empty")

    selected_dir = _select_data_directory()
    if selected_dir is None:
        print("No directory selected.")
        return

    file_labels, file_by_label = _available_lua_files(selected_dir)
    selected_labels = _select_files(file_labels, selected_dir, query)
    if not selected_labels:
        print("No file selected.")
        return

    selected_files = [file_by_label[label] for label in selected_labels]
    action = _select_action(selected_files)
    if action is None:
        print("No action selected.")
        return

    if action == "dofile":
        _print_dofile_commands(selected_files)
        return
    if action == "info":
        _show_info(selected_files)
        return
    if action == "delete":
        _delete_files(selected_files)
        return

    raise RuntimeError(f"Unsupported action: {action}")

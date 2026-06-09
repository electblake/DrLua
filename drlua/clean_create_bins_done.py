from __future__ import annotations

from pathlib import Path

import typer
from loguru import logger

from drlua.config import PROCESSED_DATA_DIR
from drlua.helpers.luautil import lua_list, read_lua_file
from drlua.copy import _copy_to_clipboard


clean_create_bins_done_app = typer.Typer()


def _find_create_bins_files() -> list[Path]:
    source_dir = PROCESSED_DATA_DIR / "create_bins"
    if not source_dir.exists():
        return []
    return sorted(source_dir.glob("*.lua"), key=lambda path: path.name.casefold())


def render_lua(files: list[Path]) -> str:
    lines = [
        f"CREATE_BINS_LUA_FILES = {lua_list([str(path.resolve()) for path in files])}",
        "",
    ]
    lines.extend(read_lua_file("clean_create_bins_done.lua").splitlines())
    return "\n".join(lines)


@clean_create_bins_done_app.command("clean-create-bins-done")
def clean_create_bins_done(
) -> None:
    files = _find_create_bins_files()
    if not files:
        raise RuntimeError(f"No create_bins Lua files found under {PROCESSED_DATA_DIR / 'create_bins'}")

    lua_text = render_lua(files)
    if not _copy_to_clipboard(lua_text):
        raise RuntimeError("Clipboard copy failed")

    logger.success("Copied clean-create-bins-done Lua script to clipboard")
    typer.echo("Copied clean-create-bins-done Lua script to clipboard.")

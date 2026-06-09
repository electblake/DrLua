from __future__ import annotations

import typer
from loguru import logger

from drlua.copy import _copy_to_clipboard
from drlua.helpers.luautil import read_lua_file


clean_short_clips_app = typer.Typer()


def render_lua(max_frames: int) -> str:
    lines = [
        f"SHORT_CLIP_MAX_FRAMES = {int(max_frames)}",
        "",
    ]
    lines.extend(read_lua_file("clean_short_clips.lua").splitlines())
    return "\n".join(lines)


@clean_short_clips_app.command("clean-short-clips")
def clean_short_clips(
    max_frames: int = typer.Option(12, "--max-frames", min=1, help="Delete clips with duration <= this frame count."),
) -> None:
    lua_text = render_lua(max_frames)
    if not _copy_to_clipboard(lua_text):
        raise RuntimeError("Clipboard copy failed")

    logger.success(f"Copied clean-short-clips Lua script to clipboard (max_frames={max_frames})")
    typer.echo(f"Copied clean-short-clips Lua script to clipboard (max_frames={max_frames}).")

from __future__ import annotations

import csv
import shutil

from pathlib import Path

import typer

from drlua.config import DateFormatTyperOption, SUPPORTED_EXTENSIONS
from drlua.create_bins import build_release_name, collect_clip_inputs, infer_source_root, write_bins_script


create_from_efu_app = typer.Typer()


def _iter_efu_media_files(efu_file: Path):
    with efu_file.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        header = next(reader, None)
        if header is None or not header or header[0] != "Filename":
            raise RuntimeError(f"Unsupported EFU header in {efu_file}")

        for row in reader:
            if not row:
                continue
            raw_path = row[0].strip()
            if not raw_path:
                continue

            media_file = Path(raw_path).expanduser()
            if media_file.suffix.lower() not in SUPPORTED_EXTENSIONS:
                continue
            if not media_file.exists() or not media_file.is_file():
                continue
            yield media_file.resolve()


@create_from_efu_app.command("create-from-efu")
def create_from_efu(
    efu_file: Path = typer.Argument(..., exists=True, dir_okay=False, file_okay=True, resolve_path=True),
    name: str = typer.Option(..., "--name"),
    section: str | None = typer.Option(None, "--section"),
    group_name: str | None = typer.Option(None, "--group"),
    tag: list[str] = typer.Option([], "--tag"),
    date_format: DateFormatTyperOption = typer.Option(DateFormatTyperOption.long, "--date", show_default=True),
    copy: bool = typer.Option(False, "--copy", metavar="FLAG"),
    only_bins: bool = typer.Option(False, "--only-bins", metavar="FLAG", show_default=True),
):
    ffprobe_path = shutil.which("ffprobe")
    if not ffprobe_path:
        raise RuntimeError(f"ffprobe not found: {ffprobe_path}")

    media_files = list(_iter_efu_media_files(efu_file))
    if not media_files:
        raise RuntimeError(f"No supported existing media files found in EFU export: {efu_file}")

    clips, media_file_count = collect_clip_inputs(media_files, ffprobe_path, progress_desc="efu+ffprobe")
    if media_file_count == 0:
        raise RuntimeError(f"No supported media files found in EFU export: {efu_file}")
    if not clips:
        raise RuntimeError(f"No readable video clips found in EFU export: {efu_file}")

    release_name = build_release_name(name, tag, section, group_name, date_format)
    source_root = infer_source_root(media_files, efu_file)
    write_bins_script(source_root, release_name, clips, only_bins, copy)

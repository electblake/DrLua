from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess

from datetime import datetime
from fractions import Fraction
from pathlib import Path

from loguru import logger
import typer
from tqdm import tqdm

from drlua.config import PROCESSED_DATA_DIR, DateFormatTyperOption, SUPPORTED_EXTENSIONS
from drlua.create_bins import render_lua
from drlua.helpers import luautil
from drlua.helpers.binutil import ClipBinGroup, ClipDataInput
from drlua.helpers.scenerules import NameTag, ReleaseName


create_from_efu_app = typer.Typer()


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

    media_files: list[Path] = []
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
            media_files.append(media_file.resolve())

    if not media_files:
        raise RuntimeError(f"No supported existing media files found in EFU export: {efu_file}")

    clips: list[ClipDataInput] = []
    media_file_count = 0
    for media_file in tqdm(media_files, desc="efu+ffprobe", unit="clip", position=0):
        media_file_count += 1
        result = subprocess.run(
            [
                ffprobe_path,
                "-v",
                "error",
                "-show_entries",
                "stream=codec_type,codec_name,width,height,nb_frames,avg_frame_rate,r_frame_rate,duration:format=duration",
                "-of",
                "json",
                str(media_file),
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            continue

        file_stat = media_file.stat()
        file_size = file_stat.st_size
        file_ext = media_file.suffix.lower()
        file_birth_ts = getattr(file_stat, "st_birthtime", file_stat.st_mtime)
        file_birth_date = datetime.fromtimestamp(file_birth_ts).isoformat(timespec="seconds")

        try:
            payload = json.loads(result.stdout)
            streams = payload.get("streams") or []
            video_stream = next((item for item in streams if item.get("codec_type") == "video"), None)
            if video_stream is None:
                raise ValueError("missing video stream")
            audio_stream = next((item for item in streams if item.get("codec_type") == "audio"), None)

            width = int(video_stream.get("width") or 0)
            height = int(video_stream.get("height") or 0)
            fps_text = video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate") or "0/0"
            fps = float(Fraction(str(fps_text))) if fps_text not in {"0/0", "", "0"} else 0.0
            frames_text = str(video_stream.get("nb_frames") or "").strip()
            frames = int(frames_text) if frames_text.isdigit() else 0
            duration = float(video_stream.get("duration") or (payload.get("format") or {}).get("duration") or 0)
            video_codec = str(video_stream.get("codec_name") or "unknown")
            audio_codec = str(audio_stream.get("codec_name") or "noaudio") if audio_stream else "noaudio"
            if not frames:
                frames = round(float(duration) * fps) if fps and duration else 0
            if frames <= 0:
                raise ValueError("missing usable frame metadata")
        except Exception:
            continue

        clips.append(
            ClipDataInput(
                path=media_file,
                frames=frames,
                fps=fps,
                video_codec=video_codec,
                audio_codec=audio_codec,
                width=width,
                height=height,
                kind="Vertical" if height > width else "Full",
                file_size=file_size,
                file_ext=file_ext,
                file_created=file_birth_date,
            )
        )

    if media_file_count == 0:
        raise RuntimeError(f"No supported media files found in EFU export: {efu_file}")
    if not clips:
        raise RuntimeError(f"No readable video clips found in EFU export: {efu_file}")
    if len(clips) < 3:
        raise RuntimeError(f"Need at least 3 readable video clips; found {len(clips)}.")

    release_name = ReleaseName()
    release_name.addRoleValue(NameTag.Role.Name, name)
    if date_format == DateFormatTyperOption.long:
        release_name.addRoleValue(NameTag.Role.LongDate, True)
    elif date_format == DateFormatTyperOption.short:
        release_name.addRoleValue(NameTag.Role.ShortDate, True)
    for item in tag:
        release_name.addRoleValue(NameTag.Role.Tag, item)
    release_name.addRoleValue(NameTag.Role.Section, section)
    release_name.addRoleValue(NameTag.Role.Group, group_name)

    drive_names = {path.drive.casefold() for path in media_files}
    if len(drive_names) == 1:
        source_root = Path(os.path.commonpath([str(path) for path in media_files]))
    else:
        source_root = efu_file

    grouped_bins = [{"clips": [], "total_frames": 0} for _ in range(3)]
    for clip in sorted(clips, key=lambda item: (-item.frames, item.path.name.lower())):
        group = min(grouped_bins, key=lambda item: (item["total_frames"], len(item["clips"])))
        group["clips"].append(clip)
        group["total_frames"] += clip.frames

    parent_name = release_name.parent_text()
    date_text = release_name.textWithRole(NameTag.Role.LongDate) or release_name.textWithRole(NameTag.Role.ShortDate)
    title_text = release_name.textWithRole(NameTag.Role.Title)
    release_text = release_name.text()
    tags = [tag_item.text() for tag_item in release_name.tagsWithRole(NameTag.Role.Tag)]
    section_text = release_name.textWithRole(NameTag.Role.Section)
    group_text = release_name.textWithRole(NameTag.Role.Group)

    output_bins: list[ClipBinGroup] = []
    for layer, bucket in enumerate(sorted(grouped_bins, key=lambda item: item["total_frames"]), start=1):
        vertical = [clip for clip in bucket["clips"] if clip.kind == "Vertical"]
        full = [clip for clip in bucket["clips"] if clip.kind == "Full"]
        vertical.sort(key=lambda item: (item.frames, item.path.name.lower()))
        full.sort(key=lambda item: (item.frames, item.path.name.lower()))
        output_bins.extend(
            [
                ClipBinGroup(
                    kind="Vertical",
                    parent=parent_name,
                    date=date_text,
                    title=title_text,
                    release_name=release_text,
                    tags=tags or None,
                    section=section_text,
                    group=group_text,
                    layer=layer,
                    clips=vertical,
                    total_frames=sum(clip.frames for clip in vertical),
                ),
                ClipBinGroup(
                    kind="Full",
                    parent=parent_name,
                    date=date_text,
                    title=title_text,
                    release_name=release_text,
                    tags=tags or None,
                    section=section_text,
                    group=group_text,
                    layer=layer,
                    clips=full,
                    total_frames=sum(clip.frames for clip in full),
                ),
            ]
        )

    output_path = PROCESSED_DATA_DIR / "create_bins" / release_name.file_name()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        render_lua(output_path, source_root, release_name, output_bins, not only_bins, ["Vertical", "Full"]),
        encoding="utf-8",
        newline="\n",
    )

    typer.echo(f"Wrote Lua script: {output_path}")
    logger.success(f"Wrote Lua script: {output_path}")
    typer.echo(luautil.lua_dofile_hint(output_path, copy))

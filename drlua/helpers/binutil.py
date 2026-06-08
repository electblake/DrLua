from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from drlua.config import BIN_COUNT
from drlua.helpers.scenerules import NameTag, ReleaseName

@dataclass
class ClipDataInput:
    path: Path
    frames: int
    fps: float
    video_codec: str
    audio_codec: str
    width: int
    height: int
    kind: str
    file_size: int
    file_ext: str
    file_created: str


@dataclass
class ClipBinGroup:
    parent: str
    date: str|None
    title: str|None
    release_name: str
    tags: list[str]|None
    section: str|None
    group: str|None
    kind: str
    layer: int
    clips: list[ClipDataInput]
    total_frames: int

def organize_bins(
    clips: list[ClipDataInput],
    release_name: ReleaseName,
    bin_count: int = BIN_COUNT,
) -> list[ClipBinGroup]:
    if len(clips) < bin_count:
        raise RuntimeError(f"Need at least {bin_count} readable video clips; found {len(clips)}.")

    bins = [{"name": f"Bin {index + 1}", "clips": [], "total_frames": 0} for index in range(bin_count)]
    for clip in sorted(clips, key=lambda item: (-item.frames, item.path.name.lower())):
        group = min(bins, key=lambda item: (item["total_frames"], len(item["clips"])))
        group["clips"].append(clip)
        group["total_frames"] += clip.frames

    output_bins: list[ClipBinGroup] = []
    parent_name = release_name.parent_text()
    date_text = (
        release_name.textWithRole(NameTag.Role.LongDate)
        or release_name.textWithRole(NameTag.Role.ShortDate)
    )
    title_text = release_name.textWithRole(NameTag.Role.Title)
    release_text = release_name.text()
    tags = [tag.text() for tag in release_name.tagsWithRole(NameTag.Role.Tag)]
    section_text = release_name.textWithRole(NameTag.Role.Section)
    group_text = release_name.textWithRole(NameTag.Role.Group)

    bins = sorted(bins, key=lambda item: item["total_frames"])
    for layer, (_suffix, bucket) in enumerate(zip(("A", "B", "C"), bins, strict=True), start=1):
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
    for bin_group in output_bins:
        logger.debug(f"{bin_group.parent}: {len(bin_group.clips)} clips, {bin_group.total_frames} total frames")
    return output_bins

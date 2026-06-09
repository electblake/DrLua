from dataclasses import dataclass
from pathlib import Path

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

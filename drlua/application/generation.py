from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import re
from PySide6.QtCore import QUrl

from drlua.create_bins import create_bins
from drlua.profile import profile


def split_sources(text: str) -> list[str]:
    values = [value.strip() for value in re.split(r"[|\r\n]+", text) if value.strip()]
    return [QUrl(value).toLocalFile() if value.startswith("file:") else value for value in values]


def split_tags(text: str) -> list[str]:
    return [value.strip() for value in re.split(r"[\r\n,]", text) if value.strip()]


def default_name(source: str) -> str:
    path = Path(source).expanduser().resolve()
    return path.name if path.is_dir() else path.stem


@dataclass(frozen=True)
class GenerationRequest:
    sources: tuple[Path, ...]
    name: str
    section: str
    group: str
    tags: tuple[str, ...]
    output_directory: Path = profile.save_directory
    recursive: bool = True

    def execute(self, progress: Callable[[str, int, int], None], activity=None) -> Path | None:
        return create_bins(
            list(self.sources),
            name=self.name,
            section=self.section,
            group_name=self.group or None,
            tag=list(self.tags),
            recursive=self.recursive,
            progress=progress,
            output_directory=self.output_directory,
            activity=activity,
        )

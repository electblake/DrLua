from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
import re

from drlua.create_bins import create_bins


def split_sources(text: str) -> list[str]:
    return [value.strip() for value in re.split(r"[|\r\n]+", text) if value.strip()]


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

    def execute(self, progress: Callable[[str, int, int], None]) -> None:
        create_bins(
            list(self.sources),
            name=self.name,
            section=self.section,
            group_name=self.group or None,
            tag=list(self.tags),
            progress=progress,
        )

from __future__ import annotations

import re
from typing import Any, Mapping


_FIELD_PATTERNS: dict[str, re.Pattern[str]] = {
    "year": re.compile(r"(?!^)[1,2]\d{3}"),
    "resolution": re.compile(r"\d{3,4}p", re.IGNORECASE),
    "type": re.compile(
        r"CAM|TS(?!C)|TELESYNC|(DVD|BD)SCR|SCR|DDC|R5[\.\s]LINE|R5|(DVD|HD|BR|BD|WEB)Rip|DVDR|(HD|PD)TV|WEB-DL|WEBDL|BluRay",
        re.IGNORECASE,
    ),
    "video": re.compile(r"NTSC|PAL|[xh][\.\s]?264", re.IGNORECASE),
    "audio": re.compile(r"AAC2[\.\s]0|AAC|AC3|DTS|DD5[\.\s]1", re.IGNORECASE),
    "language": re.compile(
        r"MULTiSUBS|MULTi|NORDiC|DANiSH|SWEDiSH|NORWEGiAN|GERMAN|iTALiAN|FRENCH|SPANiSH",
        re.IGNORECASE,
    ),
    "edition": re.compile(
        r"UNRATED|DC|(Directors|EXTENDED)[\.\s](CUT|EDITION)|EXTENDED|3D|2D|\bNF\b",
        re.IGNORECASE,
    ),
    "release": re.compile(
        r"REAL[\.\s]PROPER|PROPER|REPACK|READNFO|READ[\.\s]NFO|DiRFiX|NFOFiX",
        re.IGNORECASE,
    ),
    "group": re.compile(r"[A-Za-z0-9]+$"),
}
_TAGS_PATTERN = re.compile(r"COMPLETE|LiMiTED|iNTERNAL")
_FIELD_ORDER = (
    "title",
    "year",
    "resolution",
    "type",
    "video",
    "audio",
    "language",
    "edition",
    "tags",
    "release",
)
_NORMALIZE_DOT_SPACE_FIELDS = {"edition", "release"}


def _match_value(pattern: re.Pattern[str], text: str) -> str | None:
    match = pattern.search(text)
    return match.group(0) if match else None


def _scene_token(value: Any) -> str:
    text = str(value).strip()
    text = re.sub(r"[\s._-]+", ".", text)
    return text.strip(".-")


def parse_scene_release(name: str) -> dict[str, Any]:
    data: dict[str, Any] = {
        key: _match_value(pattern, name) for key, pattern in _FIELD_PATTERNS.items()
    }
    data["tags"] = _TAGS_PATTERN.findall(name) or None

    matched_tokens: list[str] = []
    for value in data.values():
        if isinstance(value, list):
            matched_tokens.extend(value)
        elif value:
            matched_tokens.append(value)

    title_source = name
    for token in sorted(set(matched_tokens), key=len, reverse=True):
        title_source = title_source.replace(token, "")

    title = re.sub(r"[.-]+", " ", title_source)
    title = re.sub(r"\s{2,}", " ", title).strip()

    data["title"] = title
    data["original"] = name

    cleaned: dict[str, Any] = {}
    for key, value in data.items():
        if not value:
            continue
        if key in _NORMALIZE_DOT_SPACE_FIELDS:
            value = re.sub(r"\.", " ", str(value)).strip()
        cleaned[key] = value
    return cleaned


def scene_release_to_string(data: Mapping[str, Any]) -> str:
    parts: list[str] = []
    for key in _FIELD_ORDER:
        value = data.get(key)
        if not value:
            continue
        if isinstance(value, (list, tuple, set)):
            parts.extend(_scene_token(item) for item in value if item)
            continue
        parts.append(_scene_token(value))

    release_name = ".".join(part for part in parts if part)
    group = data.get("group")
    if group:
        return f"{release_name}-{_scene_token(group)}" if release_name else _scene_token(group)
    return release_name

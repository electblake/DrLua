from pathlib import Path
import re
from PySide6.QtCore import QThread

from drlua.section_category_data import SECTION_CATEGORY_DATA


def section_options() -> list[str]:
    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    return list(sections) if isinstance(sections, dict) else []


def section_data(section: str) -> dict:
    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    if not isinstance(sections, dict):
        return {}
    value = sections.get(section, {})
    return value if isinstance(value, dict) else {}


def category_data(section: str, category: str) -> dict:
    categories = section_data(section).get("Categories", {})
    if not isinstance(categories, dict):
        return {}
    value = categories.get(category, {})
    return value if isinstance(value, dict) else {}


def category_options(section: str) -> list[str]:
    categories = section_data(section).get("Categories", {})
    if isinstance(categories, dict) and categories:
        return list(categories)

    section_path = str(section_data(section).get("Path", "")).strip()
    if not section_path:
        return []

    root = Path(section_path).expanduser()
    if not root.is_dir():
        return []

    return sorted(child.name for child in root.iterdir() if child.is_dir())


def category_tags(section: str, category: str) -> list[str]:
    data = category_data(section, category)
    raw_tags = data.get("Tags")
    if isinstance(raw_tags, list) and raw_tags:
        return [str(tag).strip() for tag in raw_tags if str(tag).strip()]
    return [category] if category else []


def match_section_category(path_value: str) -> tuple[str | None, str | None]:
    selected_path = Path(path_value).expanduser()
    selected_display = str(
        selected_path.resolve() if selected_path.exists() else selected_path
    ).rstrip("\\/")
    selected_text = selected_display.casefold()
    best_section: str | None = None
    best_category: str | None = None
    best_length = -1

    sections = SECTION_CATEGORY_DATA.get("Sections", {})
    if not isinstance(sections, dict):
        return None, None

    for section, raw_section_data in sections.items():
        if QThread.currentThread().isInterruptionRequested():
            return
        if not isinstance(raw_section_data, dict):
            continue

        section_path = str(raw_section_data.get("Path", "")).rstrip("\\/")
        if (
            path_is_under(selected_text, section_path)
            and len(section_path) > best_length
        ):
            best_section = str(section)
            best_category = category_from_section_path(selected_display, section_path)
            best_length = len(section_path)

        categories = raw_section_data.get("Categories", {})
        if not isinstance(categories, dict):
            continue
        for category, raw_category_data in categories.items():
            if QThread.currentThread().isInterruptionRequested():
                return
            if not isinstance(raw_category_data, dict):
                continue
            category_path = str(raw_category_data.get("Path", "")).rstrip("\\/")
            if (
                path_is_under(selected_text, category_path)
                and len(category_path) > best_length
            ):
                best_section = str(section)
                best_category = str(category)
                best_length = len(category_path)

    return best_section, best_category


def category_from_section_path(selected_path: str, section_path: str) -> str | None:
    if not section_path:
        return None

    relative = selected_path[len(section_path.rstrip("\\/")) :].lstrip("\\/")
    if not relative:
        return None
    return re.split(r"[\\/]", relative, maxsplit=1)[0] or None


def path_is_under(selected_text: str, root_path: str) -> bool:
    if not root_path:
        return False
    root_text = root_path.casefold()
    return (
        selected_text == root_text
        or selected_text.startswith(f"{root_text}\\")
        or selected_text.startswith(f"{root_text}/")
    )

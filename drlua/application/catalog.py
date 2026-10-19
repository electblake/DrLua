from drlua.section_category_data import SECTION_CATEGORY_DATA


def section_options() -> list[str]:
    return list(SECTION_CATEGORY_DATA)


def category_options(section: str) -> list[str]:
    return list(SECTION_CATEGORY_DATA[section])

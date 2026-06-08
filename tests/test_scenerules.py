from __future__ import annotations

from drlua.helpers.scenerules import NameTag


def test_part_name_sorts_by_weight_with_higher_weights_lower() -> None:
    parts = [
        NameTag("Group", role=NameTag.Role.Group),
        NameTag("XXX", role=NameTag.Role.Section),
        NameTag("Goon", role=NameTag.Role.Tag),
        NameTag("2026.06.07", role=NameTag.Role.Date),
        NameTag("Sunny.Rayxo", role=NameTag.Role.Name),
    ]

    assert [str(part) for part in sorted(parts)] == [
        "Sunny.Rayxo",
        "2026.06.07",
        "Goon",
        "XXX",
        "Group",
    ]


def test_section_name_normalizes_to_uppercase() -> None:
    assert str(NameTag("XXX", role=NameTag.Role.Section)) == "XXX"
    assert str(NameTag("Games", role=NameTag.Role.Section)) == "GAMES"
    assert str(NameTag("0day", role=NameTag.Role.Section)) == "0DAY"
    assert str(NameTag("mobile games", role=NameTag.Role.Section)) == "MOBILE.GAMES"


def test_make_release_name_uses_class_normalization() -> None:
    result = NameTag.make_release_name(
        [
            (NameTag.Role.Section, "XXX"),
            (NameTag.Role.Name, "Sunny.Rayxo"),
            (NameTag.Role.Date, "2026.06.07"),
            (NameTag.Role.Tag, ["Goon", "Brunette"]),
        ]
    )

    assert result == "XXX.Sunny.Rayxo.2026.06.07.Goon.Brunette"


def test_make_release_slug_is_class_based() -> None:
    assert NameTag.make_release_slug("XXX.Sunny.Rayxo.2026.06.07.Goon.Brunette") == "xxx.sunny.rayxo.2026.06.07.goon.brunette"


def test_make_release_name_without_section_matches_previous_behavior() -> None:
    result = NameTag.make_release_name(
        [
            (NameTag.Role.Name, "Sunny.Rayxo"),
            (NameTag.Role.Date, "2026.06.07"),
            (NameTag.Role.Tag, ["Goon", "Brunette"]),
        ]
    )

    assert result == "Sunny.Rayxo.2026.06.07.Goon.Brunette"

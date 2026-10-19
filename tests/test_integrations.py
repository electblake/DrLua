import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from drlua import integrations


@pytest.mark.parametrize("frozen", [False, True])
def test_install_overwrites_all_contexts_with_quoted_absolute_paths(monkeypatch, tmp_path, frozen):
    registry = MagicMock()
    values = {}
    registry.CreateKeyEx.side_effect = lambda hive, key, reserved, access: MagicMock(
        __enter__=lambda self: key, __exit__=lambda *args: None
    )
    registry.SetValueEx.side_effect = lambda key, name, reserved, kind, value: values.__setitem__((key, name), value)
    monkeypatch.setitem(sys.modules, "winreg", registry)
    executable = tmp_path / "App with spaces" / "DrLua.exe"
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "frozen", frozen, raising=False)
    extraction = tmp_path / "Extracted app with spaces"
    monkeypatch.setattr(sys, "_MEIPASS", str(extraction), raising=False)

    for _ in range(2):
        assert integrations.install() == 0
        assert len(values) == 9
        for root, target in integrations.CONTEXTS:
            key = rf"{root}\DrLua"
            assert values[key, ""] == "Open in DrLua"
            icon_root = extraction if frozen else Path(integrations.__file__).resolve().parent
            assert values[key, "Icon"] == f'"{icon_root / integrations.ICON_NAME}"'
            launcher = f'"{executable.resolve()}"'
            if not frozen:
                launcher += ' "-I" "-m" "drlua.gui"'
                assert (icon_root / integrations.ICON_NAME).is_file()
            assert values[key + r"\command", ""] == f'{launcher} "{target}"'

    assert registry.CreateKeyEx.call_count == 12
    assert all(call.args[0] == registry.HKEY_CURRENT_USER for call in registry.CreateKeyEx.call_args_list)

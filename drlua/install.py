from pathlib import Path
import shutil
import sys


MENU_ENTRIES = (
    {
        "key": "DrLua",
        "label": "Run DrLua",
        "args": (),
        "keep_console": True,
    },
    {
        "key": "DrLuaInteractive",
        "label": "Run DrLua (Interactive)",
        "args": ("--interactive",),
        "keep_console": True,
    },
)

MENU_CONTEXTS = (
    (r"Software\Classes\Directory\shell", "%1"),
    (r"Software\Classes\Directory\Background\shell", "%V"),
    (r"Software\Classes\Drive\shell", "%1"),
)


def _launcher_command() -> list[str]:
    if getattr(sys, "frozen", False):
        return [str(Path(sys.executable).resolve())]

    argv_launcher = Path(sys.argv[0])
    if argv_launcher.exists() and argv_launcher.suffix.lower() in {".exe", ".bat", ".cmd"}:
        return [str(argv_launcher.resolve())]

    for command_name in ("drlua.exe", "drlua"):
        launcher = shutil.which(command_name)
        if launcher:
            return [str(Path(launcher).resolve())]

    return [str(Path(sys.executable).resolve()), "-m", "drlua.cli"]


def _menu_key(root: str, name: str):
    return rf"{root}\{name}"


def _quote(part: str) -> str:
    return f'"{part}"'


def _raw_command_value(command: list[str], args: tuple[str, ...], target_arg: str) -> str:
    return " ".join(_quote(part) for part in [*command, *args, target_arg])


def _command_value(command: list[str], args: tuple[str, ...], target_arg: str, *, keep_console: bool) -> str:
    raw_command = _raw_command_value(command, args, target_arg)
    if not keep_console:
        return raw_command
    return f'{_quote(str(Path("cmd.exe")))} /d /k "{raw_command}"'


def _delete_key_if_exists(winreg, key_path: str) -> None:
    try:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
    except FileNotFoundError:
        pass


def install(help=""):
    """Register drlua in the Windows explorer context menu."""
    import winreg

    launcher_command = _launcher_command()
    launcher_icon = launcher_command[0]

    for root, target_arg in MENU_CONTEXTS:
        for entry in MENU_ENTRIES:
            menu_key = _menu_key(root, entry["key"])
            command_value = _command_value(
                launcher_command,
                entry["args"],
                target_arg,
                keep_console=entry["keep_console"],
            )
            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, menu_key, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, entry["label"])
                winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, launcher_icon)
            with winreg.CreateKeyEx(
                winreg.HKEY_CURRENT_USER,
                menu_key + r"\command",
                0,
                winreg.KEY_SET_VALUE,
            ) as key:
                winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command_value)

    print(f"[OK] Installed {len(MENU_ENTRIES) * len(MENU_CONTEXTS)} context menu entry(s): {launcher_command[0]}")
    return 0


def uninstall():
    import winreg

    for root, _target_arg in MENU_CONTEXTS:
        for entry in MENU_ENTRIES:
            menu_key = _menu_key(root, entry["key"])
            _delete_key_if_exists(winreg, menu_key + r"\command")
            _delete_key_if_exists(winreg, menu_key)

    print(f"[OK] Removed {len(MENU_ENTRIES) * len(MENU_CONTEXTS)} DrLua context menu entry(s).")
    return 0

from pathlib import Path
import sys


MENU_KEY = "DrLua"
MENU_LABEL = "Run DrLua"


def _launcher_exe():
    return Path(sys.executable).resolve()


def _menu_key(name):
    return rf"Software\Classes\Directory\shell\{name}"


def install(help=""):
    """Register drlua in the Windows explorer context menu."""
    import winreg

    launcher = _launcher_exe()
    command_value = f"\"{launcher}\" \"%1\""
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, _menu_key(MENU_KEY), 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, MENU_LABEL)
        winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, str(launcher))
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER,
        _menu_key(MENU_KEY) + r"\command",
        0,
        winreg.KEY_SET_VALUE,
    ) as key:
        winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command_value)
    print(f"[OK] Installed context menu entry: {launcher}")
    return 0


def uninstall():
    import winreg

    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _menu_key(MENU_KEY) + r"\command")
    winreg.DeleteKey(winreg.HKEY_CURRENT_USER, _menu_key(MENU_KEY))
    print("[OK] Removed DrLua context menu entry.")
    return 0

import sys
from pathlib import Path

from loguru import logger

APP_NAME = "DrLua"
APP_MODULE = "drlua.gui"
ICON_NAME = "DrLua-app-icon.ico"

CONTEXTS = (
    (r"Software\Classes\Directory\shell", "%1"),
    (r"Software\Classes\Directory\Background\shell", "%V"),
    (r"Software\Classes\Drive\shell", "%1"),
)


def install():
    import winreg

    executable = str(Path(sys.executable).resolve())
    if getattr(sys, "frozen", False):
        launcher = [executable]
        icon_root = Path(sys._MEIPASS)
    else:
        launcher = [executable, "-I", "-m", APP_MODULE]
        icon_root = Path(__file__).resolve().parent

    icon = f'"{icon_root / ICON_NAME}"'

    for root, target in CONTEXTS:
        menu_key = rf"{root}\{APP_NAME}"
        command = " ".join(f'"{part}"' for part in [*launcher, target])
        logger.info(f"File Explorer command ({root}): {command}")

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, menu_key, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f"Open in {APP_NAME}")
            winreg.SetValueEx(key, "Icon", 0, winreg.REG_SZ, icon)

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER,
            menu_key + r"\command",
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, command)

    logger.info(f"[OK] Installed {len(CONTEXTS)} File Explorer context menu entries.")
    return 0

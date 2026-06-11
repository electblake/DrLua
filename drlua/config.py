import enum
from importlib import resources
from pathlib import Path

from loguru import logger
from platformdirs import PlatformDirs

dirs = PlatformDirs("DrLua", "DrLua")

# Paths
PROJ_ROOT = dirs.user_config_path
LUA_DIR = PROJ_ROOT / "lua"
SCRIPTS_DIR = PROJ_ROOT / "scripts"
logger.trace(f"PROJ_ROOT path is: {PROJ_ROOT}")
PROJ_ROOT.mkdir(exist_ok=True, parents=True)
LUA_DIR.mkdir(exist_ok=True, parents=True)
SCRIPTS_DIR.mkdir(exist_ok=True, parents=True)

STASH_MAP = {
    "/X3": "X:"
}

DATA_DIR = dirs.user_data_path
logger.trace(f"DATA_DIR path is: {DATA_DIR}")
if not DATA_DIR.exists():
    DATA_DIR.mkdir(exist_ok=True, parents=True)

RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

SCENE_NAME_SEP = "."
lib_lua_path = LUA_DIR / "lib.lua"
enter_interactive_path = SCRIPTS_DIR / "Enter-Interactive.ps1"
categories_path = SCRIPTS_DIR / "Categories.psd1"


def _read_packaged_lib_lua() -> str:
    candidates = []

    try:
        candidates.append(resources.files("drlua").joinpath("lua", "lib.lua"))
    except Exception:
        logger.exception("Failed to resolve drlua package resources")

    candidates.append(Path(__file__).resolve().parent / "lua" / "lib.lua")

    for candidate in candidates:
        try:
            return candidate.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        "Could not locate bundled resource 'drlua/lua/lib.lua'. "
        "If this is a PyInstaller build, include drlua package data."
    )


def sync_packaged_lib_lua(target_path: Path = lib_lua_path) -> str:
    packaged_lib_lua_text = _read_packaged_lib_lua()
    if not target_path.exists() or target_path.read_text(encoding="utf-8") != packaged_lib_lua_text:
        target_path.parent.mkdir(exist_ok=True, parents=True)
        target_path.write_text(packaged_lib_lua_text, encoding="utf-8", newline="\n")
    return packaged_lib_lua_text


def _read_packaged_script(filename: str) -> str:
    candidates = []

    try:
        candidates.append(resources.files("drlua").joinpath("scripts", filename))
    except Exception:
        logger.exception("Failed to resolve drlua script resources")

    candidates.append(Path(__file__).resolve().parent.parent / "scripts" / filename)

    for candidate in candidates:
        try:
            return candidate.read_text(encoding="utf-8")
        except FileNotFoundError:
            continue

    raise FileNotFoundError(
        f"Could not locate bundled resource 'drlua/scripts/{filename}'. "
        "If this is a PyInstaller build, include drlua script data."
    )


def sync_packaged_script(filename: str, target_path: Path) -> str:
    packaged_script_text = _read_packaged_script(filename)
    if not target_path.exists() or target_path.read_text(encoding="utf-8") != packaged_script_text:
        target_path.parent.mkdir(exist_ok=True, parents=True)
        target_path.write_text(packaged_script_text, encoding="utf-8", newline="\n")
    return packaged_script_text


sync_packaged_lib_lua()
sync_packaged_script("Enter-Interactive.ps1", enter_interactive_path)
sync_packaged_script("Categories.psd1", categories_path)

# If tqdm is installed, configure loguru with tqdm.write
# https://github.com/Delgan/loguru/issues/135
try:
    from tqdm import tqdm

    logger.remove(0)
    logger.add(lambda msg: tqdm.write(msg, end=""), colorize=True)
except ModuleNotFoundError:
    pass

class DateFormatTyperOption(enum.Enum):
    long = 'long'
    short = 'short'

BIN_COUNT = 3
SUPPORTED_EXTENSIONS = {
    ".3g2",
    ".3gp",
    ".avi",
    ".braw",
    ".m2t",
    ".m2ts",
    ".m4v",
    ".mkv",
    ".mov",
    ".mp4",
    ".mpeg",
    ".mpg",
    ".mts",
    ".mxf",
    ".r3d",
    ".ts",
    ".webm",
    ".wmv",
}

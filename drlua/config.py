import enum
from importlib import resources
from pathlib import Path

from loguru import logger
from platformdirs import PlatformDirs

dirs = PlatformDirs("DrLua", "DrLua")

# Paths
PROJ_ROOT = dirs.user_config_path
LUA_DIR = PROJ_ROOT / "lua"
logger.trace(f"PROJ_ROOT path is: {PROJ_ROOT}")
PROJ_ROOT.mkdir(exist_ok=True, parents=True)
LUA_DIR.mkdir(exist_ok=True, parents=True)

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


def _iter_lua_assets(root, relative_dir: Path = Path()):
    for child in root.iterdir():
        relative_path = relative_dir / child.name
        if child.is_dir():
            yield from _iter_lua_assets(child, relative_path)
        elif child.is_file() and child.name.endswith(".lua"):
            yield child, relative_path


def _packaged_lua_root():
    candidates = []

    try:
        candidates.append(resources.files("drlua").joinpath("lua"))
    except Exception:
        logger.exception("Failed to resolve drlua package resources")

    candidates.append(Path(__file__).resolve().parent / "lua")

    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    raise FileNotFoundError(
        "Could not locate bundled resource 'drlua/lua'. "
        "If this is a PyInstaller build, include drlua package data."
    )


def sync_packaged_lua_assets(target_dir: Path = LUA_DIR) -> list[Path]:
    packaged_lua_root = _packaged_lua_root()
    synced_paths: list[Path] = []
    target_dir.mkdir(exist_ok=True, parents=True)

    for lua_asset, relative_path in _iter_lua_assets(packaged_lua_root):
        target_path = target_dir / relative_path
        target_path.parent.mkdir(exist_ok=True, parents=True)
        target_path.write_text(lua_asset.read_text(encoding="utf-8"), encoding="utf-8", newline="\n")
        synced_paths.append(target_path)

    return synced_paths


sync_packaged_lua_assets()

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

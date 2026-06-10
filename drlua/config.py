import enum
from pathlib import Path

from loguru import logger

from platformdirs import PlatformDirs

dirs = PlatformDirs("DrLua", "DrLua")

# Paths
PACKAGE_ROOT = Path(__file__).resolve().parent
PROJ_ROOT = PACKAGE_ROOT.parent
LUA_DIR = PACKAGE_ROOT / "lua"
logger.trace(f"PROJ_ROOT path is: {PROJ_ROOT}")

DATA_DIR = dirs.user_data_path
logger.trace(f"DATA_DIR path is: {DATA_DIR}")
if not DATA_DIR.exists():
    DATA_DIR.mkdir(exist_ok=True, parents=True)

RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"

SCENE_NAME_SEP = "."


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


import typer
from typing import Annotated
def version_callback(value: bool):
    if value:
        from drlua import __version__
        typer.echo(__version__)
        print(f"DrLua Version: {__version__}")
        raise typer.Exit()

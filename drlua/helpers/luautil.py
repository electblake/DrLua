from pathlib import Path
from loguru import logger
import pyperclip

from drlua.config import LUA_SHARED_DIR

def lua_string(value: str|None) -> str:
    value = value if value is not None else ""
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def lua_list(list_obj: list[str] | None) -> str:
    list_obj = list_obj if list_obj is not None else []
    return "{ " + ", ".join(lua_string(str(item)) for item in list_obj) + " }"

def lua_dofile_command(file: str | Path) -> str:
    file_path = Path(file)
    return f"\tdofile([[{file_path.resolve()}]])"

def lua_dofile_hint(file: str | Path, copy: bool = False) -> str:
    dofile = lua_dofile_command(file)
    hint = [
        "> Paste into the DaVinci Resolve Lua console:",
        "```",
        dofile,
        "```",
    ]
    hint_text = "\n".join(hint)

    if copy:
        logger.debug("Copying Lua Command to Clipboard..")
        pyperclip.copy(dofile)

    return hint_text

def read_lua_file(name: str | Path):
    name = LUA_SHARED_DIR / name
    return name.read_text()

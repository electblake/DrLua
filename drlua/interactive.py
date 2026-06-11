from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from drlua.config import enter_interactive_path


def launch_interactive(input_path: str | Path | None = None) -> int:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(enter_interactive_path),
        "-DrLuaExe",
        str(Path(sys.executable).resolve()),
    ]
    if input_path is not None:
        command.extend(["-InputPath", str(input_path)])

    return subprocess.run(command).returncode

"""Windowed entry point for the Tkinter launcher."""

from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
import sys

from platformdirs import PlatformDirs


def main() -> int:
    log_dir = PlatformDirs("DrLua", "DrLua").user_log_path
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "launcher.log").open("a", encoding="utf-8", buffering=1) as log, redirect_stdout(log), redirect_stderr(log):
        from drlua.ui.interactive import launch_interactive

        return launch_interactive([Path(value) for value in sys.argv[1:]])


if __name__ == "__main__":
    raise SystemExit(main())

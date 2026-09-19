# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from importlib.metadata import distribution
import sys
import tomllib

root = Path(SPECPATH).parent
version = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
artifact = f"DrLua-{version}-windows-amd64"
data = [
    (str(root / "drlua/lua"), "drlua/lua"),
    (str(root / "drlua/fusion"), "drlua/fusion"),
    (str(root / "build/vendor/ffprobe.exe"), "tools/ffmpeg"),
    (str(root / "build/vendor/LICENSE"), "tools/ffmpeg"),
    (str(root / "build/vendor/README.txt"), "tools/ffmpeg"),
    (str(root / "build/vendor/SHA256.txt"), "tools/ffmpeg"),
    (str(Path(sys.base_prefix) / "LICENSE.txt"), "licenses/python"),
]
for name in ("loguru", "platformdirs", "luadata", "colorama"):
    package = distribution(name)
    for file in package.files:
        if "license" in file.name.lower() or "copying" in file.name.lower():
            data.append((str(package.locate_file(file)), f"licenses/{name}/{file.parent}"))
gui = Analysis([str(root / "drlua/gui.py")], pathex=[str(root)], datas=data)
gui_exe = EXE(PYZ(gui.pure), gui.scripts, [], exclude_binaries=True,
              name="DrLua", console=False, upx=False)
COLLECT(gui_exe, gui.binaries, gui.datas, name=artifact, upx=False)

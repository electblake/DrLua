# -*- mode: python ; coding: utf-8 -*-
from importlib.metadata import distribution
from pathlib import Path
import os

qt_root = Path(distribution("PySide6-Essentials").locate_file("PySide6"))
# Resolve native dependencies from this Qt distribution and Windows, not unrelated PATH tools.
os.environ["PATH"] = os.pathsep.join((str(qt_root), str(Path(os.environ["SystemRoot"]) / "System32")))

a = Analysis(
    ['drlua\\gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('drlua\\lua', 'drlua\\lua'),
        ('drlua\\fusion\\*.setting', 'drlua\\fusion'),
        ('build/vendor/ffprobe.exe', 'tools/ffmpeg'),
        ('build/vendor/LICENSE', 'tools/ffmpeg'),
        ('build/vendor/README.txt', 'tools/ffmpeg'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', '_tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='drlua',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['drlua\\cli.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('drlua\\lua\\*.lua', 'drlua\\lua'),
        ('drlua\\fusion\\*.setting', 'drlua\\fusion'),
        ('scripts\\Enter-Interactive.ps1', 'drlua\\scripts'),
        ('scripts\\Categories.psd1', 'drlua\\scripts'),
    ],
    hiddenimports=['drlua.interactive'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

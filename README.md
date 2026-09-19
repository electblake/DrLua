# drlua v0.2.3

Creates DaVinci Resolve Lua scripts and helps manage generated .lua files.

## Desktop app

Run `uv run drlua` to open the Tkinter application.
Add folders and files, or enter one source path per line. The first source suggests
the name, section, and category. Selecting a category fills its suggested tags;
the name, section, category, group, and tags remain editable.

**Generate Lua script** generates the Lua script in the background. Copy the `dofile`
command from Output into the DaVinci Resolve Lua console. The output pane can be
resized with its divider; **Open output folder** opens the generated scripts.

## Build the Windows installer

Requires PowerShell 7, uv, Python 3.12.9, and Inno Setup 6. Supply an extracted
Windows x64 static FFmpeg distribution containing `bin/ffprobe.exe`, `LICENSE`,
and `README.txt`. The local build was tested with Gyan's FFmpeg 7.1.1 full build.
The existing local `drlua/section_category_data.py` is also required and is bundled
with its configured section/category paths; review that data before distributing.

```powershell
pwsh -NoProfile -File scripts/build-setup.ps1 -FfmpegRoot C:\Tools\ffmpeg-7.1.1-full_build
# Or:
mise run build-setup -- -FfmpegRoot C:\Tools\ffmpeg-7.1.1-full_build
```

Use `-IsccPath` to select a different Inno Setup compiler. The script creates a
clean environment from `uv.lock`, stages FFprobe and its license/provenance files,
builds `scripts/DrLua.spec` and compiles `scripts/DrLua.iss`.
It records the staged FFprobe SHA-256; the supplied distribution must be verified
by the build operator against its distributor before release.

Outputs are `dist/DrLua-<version>-windows-amd64/` and
`dist/DrLua-<version>-windows-amd64-Setup.exe`. The bundle contains `DrLua.exe`
(the Tkinter application). Installation is per-user,
with a Start menu shortcut and optional desktop shortcut; no Python installation
or network download is needed at install time. User data stays in DrLua's existing
application-data directories. The output pane tails `drlua.log` in the PlatformDirs user-log directory.
Generation runs directly in a worker thread within the application.

The `mise run compile` portable Tkinter build uses the FFprobe staged by the setup
build. Installers are unsigned; this task does not publish a new GitHub release.

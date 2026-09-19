# drlua v0.2.3

Creates DaVinci Resolve Lua scripts and helps manage generated .lua files.

## `--help`

```text
usage: drlua [-h] [--install | --uninstall] [--interactive] [--files [NAME]]
             [--name NAME] [--section SECTION] [--tag TAG] [--group GROUP]
             [--recursive | --no-recursive | -Recurse]
             [--vertical | --no-vertical | -Vertical]
             [--full | --no-full | -Full] [--bins | --no-bins | -Bins]
             [--version]
             [from_locations ...]

drlua v0.2.3

positional arguments:
  from_locations        media folders or files

options:
  -h, --help            show this help message and exit
  --install             install Windows Explorer context menu entries
  --uninstall           remove Windows Explorer context menu entries
  --interactive, -i, -Interactive
                        open the interactive Tkinter launcher
  --files [NAME], -Files [NAME]
                        interact with generated .lua files; optionally provide
                        an initial filename filter
  --name NAME, -Name NAME
  --section SECTION, -Section SECTION
  --tag TAG, -Tag TAG
  --group GROUP, -Group GROUP
  --recursive, --no-recursive, -Recurse
  --vertical, --no-vertical, -Vertical
  --full, --no-full, -Full
  --bins, --no-bins, -Bins
  --version, --Version

drlua v0.2.3
Creates DaVinci Resolve Lua scripts and helps manage generated .lua files.
```

## `--version`

```text
0.2.3
DrLua Version: 0.2.3
```

## Desktop app

Run `uv run drlua --interactive` or `uv run drlua-gui` to open the Tkinter launcher.
Add folders and files, or enter one source path per line. The first source suggests
the name, section, and category. Selecting a category fills its suggested tags;
the name, section, category, group, and tags remain editable.

**Send to DrLua** generates the Lua script in the background. Copy the `dofile`
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
builds `scripts/DrLua.spec`, checks the CLI version, and compiles `scripts/DrLua.iss`.
It records the staged FFprobe SHA-256; the supplied distribution must be verified
by the build operator against its distributor before release.

Outputs are `dist/DrLua-<version>-windows-amd64/` and
`dist/DrLua-<version>-windows-amd64-Setup.exe`. The bundle contains `DrLua.exe`
(desktop launcher) and `drlua-cli.exe` (existing CLI). Installation is per-user,
with a Start menu shortcut and optional desktop shortcut; no Python installation
or network download is needed at install time. User data stays in DrLua's existing
application-data directories. Windowed launcher logs are in the PlatformDirs
user-log directory, in `launcher.log`.

The legacy `mise run compile` portable build uses the FFprobe staged by the setup
build. Installers are unsigned; this task does not publish a new GitHub release.

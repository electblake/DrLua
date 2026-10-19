<p align="center">
  <img src="assets/Dr-Lua-color.png" alt="Dr. Lua" width="640" style="max-width: 640px; width: 100%; height: auto;">
</p>

<h1 align="center">DrLua v0.5.1</h1>

<p align="center">Create and manage Lua scripts for DaVinci Resolve.</p>

## Desktop app

Run `uv run drlua` to open the PySide6 / Qt Widgets application using the platform default style.
Add folders and files, or enter one source path per line. The first source suggests
the name. Choose a section and category from the shared options defined in
`drlua/section_category_data.py`. Selecting a category fills the tags with its name;
the name, group, and tags remain editable. Source paths never select a section or
category.

**Generate Lua script** generates the Lua script in the background. Copy the `dofile`
command from Output into the DaVinci Resolve Lua console. The output pane can be
resized with its divider; **Open output folder** opens the generated scripts.
**Copy Lua command** becomes available after generation and copies the last run's
`dofile` command. Starting another generation clears it until that run succeeds.

The Files tab lists Lua filenames in the save directory. Select one or more files
with Ctrl/Shift and choose **Copy selected commands** to copy their `dofile` calls,
one per line in filename order. The list refreshes when opened and after generation.

Drag the Generate, Files, and Settings tabs to reorder them. Settings contains the
update checker and uses a native form with an editable **Save directory**
and folder picker. QSettings persists this directory; the default is the
platformdirs user-data directory's `processed/create_bins` folder.

Run `uv run drlua -NoProfile` for an isolated session. DrLua neither reads nor
writes saved preferences and uses a fresh temporary directory for configuration,
Lua assets, logs, and default output. A directory selected during that session is
used only for that session. Temporary output is left available for use in Resolve.
This DrLua option is independent of PowerShell's `pwsh -NoProfile` option.

## Build the Windows installer

Requires PowerShell 7, uv, Python 3.12.9, and Inno Setup 6. Supply an extracted
Windows x64 static FFmpeg distribution containing `bin/ffprobe.exe`, `LICENSE`,
and `README.txt`.
`drlua/section_category_data.py` is included in the repository and bundle. It
contains only section names and category-name lists, with no paths or tag overrides.

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
(the Qt Widgets application). Installation is per-user,
with a Start menu shortcut and optional desktop shortcut; no Python installation
or network download is needed at install time. User data stays in DrLua's existing
application-data directories. Logs are written to `drlua.log` in the PlatformDirs user-log directory
and streamed to the Output pane through queued Qt signals.
Generation runs directly in a QThread within the application. FFprobe is managed
by QProcess in that worker thread. Updates also run in QThreads; the UI remains on
the Qt GUI thread. Closing the app waits for active work before releasing the
installer mutex. No separate Python process performs generation.

The `mise run compile` portable Qt build uses the FFprobe staged by the setup
build. Installers are unsigned.

## Code organization

- `drlua/application/`: catalog rules, immutable generation request, and progress calculations.
- `drlua/ui/form.py`: observable form state.
- `drlua/ui/controller.py`: Qt application actions and job coordination.
- `drlua/ui/jobs.py`: blocking operations in QThreads, with signals for progress and results.
- `drlua/ui/window.py`: native tabs, forms, menus, output, and dialogs.
- `drlua/profile.py`: QSettings preferences and no-profile session paths.
- `drlua/create_bins.py`: media collection, probing, grouping, and Lua generation.
- `drlua/updates.py`: release lookup and installer download.

Run `uv run pytest -q` to exercise application rules, updates, and the actual Qt Widgets
Generate button with the real media in `data/sample`. These desktop tests require
a Windows desktop session and FFprobe on PATH. The packaged app uses its bundled FFprobe.

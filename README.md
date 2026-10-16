# drlua v0.3.1

Creates DaVinci Resolve Lua scripts and helps manage generated .lua files.

## Desktop app

Run `uv run drlua` to open the PySide6 / Qt Quick application with FluentWinUI3 controls.
Add folders and files, or enter one source path per line. The first source suggests
the name, section, and category. Selecting a category fills its suggested tags;
the name, section, category, group, and tags remain editable.

**Generate Lua script** generates the Lua script in the background. Copy the `dofile`
command from Output into the DaVinci Resolve Lua console. The output pane can be
resized with its divider; **Open output folder** opens the generated scripts.

## Build the Windows installer

Requires PowerShell 7, uv, Python 3.12.9, and Inno Setup 6. Supply an extracted
Windows x64 static FFmpeg distribution containing `bin/ffprobe.exe`, `LICENSE`,
and `README.txt`.
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
(the Qt Quick application). Installation is per-user,
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
- `drlua/ui/form.py`: observable form state exposed to QML.
- `drlua/ui/controller.py`: Qt application actions and job coordination.
- `drlua/ui/jobs.py`: blocking operations in QThreads, with signals for progress and results.
- `drlua/ui/qml/`: window, form panels, actions, output, and update dialog.
- `drlua/create_bins.py`: media collection, probing, grouping, and Lua generation.
- `drlua/updates.py`: release lookup and installer download.

Run `uv run pytest -q` to exercise application rules, updates, and the actual QML
Generate button with the real media in `data/sample`. These desktop tests require
a Windows desktop session and FFprobe on PATH. The packaged app uses its bundled FFprobe.

Run `pwsh -File scripts/check-qml.ps1` to generate Python type metadata and lint
every QML component with zero warnings allowed.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added a Search Files field with live, case-insensitive filename filtering in the Files tab.

## [0.4.0] - 2026-10-18

### Added

- Added Generate, Files, and Settings tabs with generated Lua command copying and a saved output directory.
- Added a subdirectory scanning checkbox saved and restored through QSettings, generation cancellation, and elapsed-time and activity reporting.
- Added isolated `-NoProfile` desktop sessions with temporary storage.
- Added a Refresh button to reload saved Lua files in the Files tab.

### Changed

- Replaced Qt Quick screens with native Qt Widgets and platform-default styling.
- Moved source metadata lookup and generated-file listing into background workers.
- Reduced the source paths text area to half height and aligned its buttons with the form input column.
- Moved the save-directory input and folder buttons from Settings above the file list in the Files tab.
- Renamed the generation actions to Generate and Copy, with Cancel between them.

### Fixed

- Fixed the release task to build and publish the Windows installer with versioned changelog notes.
- Prevented pending metadata and delayed worker signals from leaving generation stuck or changing a subsequent run.
- Stopped cancelled runs before starting another scan, probe, grouping, or output-writing step.
- Discarded unfinished output on cancellation while preserving existing scripts and allowing generation to restart.

## [0.3.1] - 2026-09-19

### Changed

- Make the desktop launcher UI-only by removing the unused programmatic input-path injection path.
- Exercise the actual Generate button against real media in integration coverage, including progress and Lua output assertions.

## [0.3.0] - 2026-09-18

### Added

- Add a resizable Tkinter launcher inspired by Spectra and YOLO Media Organizer, with separate folder/file pickers, output copying, and an output-folder shortcut.
- Add a Windows installer with a windowed launcher, bundled Python runtime and FFprobe, and per-user shortcuts.
- Add in-app update checking and installer downloads, closing DrLua before launching setup.
- Add running-app checks at installer startup and immediately before installation.
- Show generation phases, completed item counts, items per second, and estimated time remaining.

### Changed

- Replace the WinForms launcher with Tkinter while preserving section/category matching, tag suggestions, and background script generation.
- Remove the unused Gooey and Python.NET runtime dependencies.
- Move the generation button, progress bar, and output-folder button below Output and above the status line.
- Link the progress bar to media processing, bin grouping, and Lua file writing.

### Removed

- Remove the console CLI and obsolete interactive, file-management, and Explorer integration modules.

## [0.2.3] - 2026-09-17

### Added

- Support multiple source folders and files in a single bin-creation command.
- Support selecting multiple files in the interactive launcher and entering source paths separated by newlines or pipes.
- Accept individual media files and Stash export JSON files as input sources.
- Add this changelog with dated release notes and version comparison links.

## [0.2.2] - 2026-08-01

### Added

- Document command-line usage, available options, and version output in the README.

### Changed

- Include the README in GitHub release notes.

## [0.2.1] - 2026-08-01

### Added

- Initial GitHub release with a standalone Windows executable.
- Generate DaVinci Resolve Lua scripts for media imports, bin organization, and timeline creation.
- Import media from folders, Everything file lists, metadata CSV files, and Stash exports.
- Provide an interactive Windows launcher, generated Lua file management, and Windows Explorer context menu integration.

[Unreleased]: https://github.com/electblake/DrLua/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/electblake/DrLua/compare/v0.3.1...v0.4.0
[0.3.1]: https://github.com/electblake/DrLua/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/electblake/DrLua/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/electblake/DrLua/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/electblake/DrLua/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/electblake/DrLua/releases/tag/v0.2.1

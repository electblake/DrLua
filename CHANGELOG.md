# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project uses [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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

[Unreleased]: https://github.com/electblake/DrLua/compare/v0.3.0...HEAD
[0.3.0]: https://github.com/electblake/DrLua/compare/v0.2.3...v0.3.0
[0.2.3]: https://github.com/electblake/DrLua/compare/v0.2.2...v0.2.3
[0.2.2]: https://github.com/electblake/DrLua/compare/v0.2.1...v0.2.2
[0.2.1]: https://github.com/electblake/DrLua/releases/tag/v0.2.1

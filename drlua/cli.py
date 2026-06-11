from __future__ import annotations

import argparse
from pathlib import Path
import sys

from drlua.create_bins import create_bins
from drlua.files import files_command
from drlua.install import install, uninstall
from drlua.interactive import launch_interactive
from drlua import __version__


CommandResult = int | None
PROGRAM_NAME = "drlua"
PROGRAM_SHORT_DESCRIPTION = f"{PROGRAM_NAME} v{__version__}"
PROGRAM_LONG_DESCRIPTION = f"""{PROGRAM_NAME} v{__version__}
Creates DaVinci Resolve Lua scripts and helps manage generated .lua files."""


def _add_create_bins_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("from_location", nargs="?", type=Path, help="media folder or export file")
    parser.add_argument("--name", "-Name")
    parser.add_argument("--section", "-Section")
    parser.add_argument("--tag", "-Tag", action="append", default=[])
    parser.add_argument("--group", "-Group")
    parser.add_argument(
        "--recursive",
        "-Recurse",
        dest="recursive",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--vertical",
        "-Vertical",
        dest="vertical_only",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument(
        "--full",
        "-Full",
        dest="full_only",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument(
        "--bins",
        "-Bins",
        dest="bins_only",
        action=argparse.BooleanOptionalAction,
        default=False,
    )
    parser.add_argument("--version", "--Version", action="store_true", default=False)


def _normalize_legacy_argv(argv: list[str]) -> list[str]:
    if not argv:
        return argv
    if argv[0] == "create-bins":
        return argv[1:]
    if argv[0] == "files":
        return ["--files", *argv[1:]]
    return argv


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog=PROGRAM_NAME,
        description=PROGRAM_SHORT_DESCRIPTION,
        epilog=PROGRAM_LONG_DESCRIPTION,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    install_group = parser.add_mutually_exclusive_group()
    install_group.add_argument("--install", action="store_true", help="install Windows Explorer context menu entries")
    install_group.add_argument("--uninstall", action="store_true", help="remove Windows Explorer context menu entries")
    parser.add_argument(
        "--files",
        "-Files",
        nargs="?",
        const=None,
        default=False,
        metavar="NAME",
        help="interact with generated .lua files; optionally provide an initial filename filter",
    )
    _add_create_bins_arguments(parser)

    return parser


def _run_create_bins(args: argparse.Namespace) -> CommandResult:
    if args.from_location is None:
        return launch_interactive()

    return create_bins(
        from_location=args.from_location,
        name=args.name,
        section=args.section,
        tag=args.tag,
        group_name=args.group,
        recursive=args.recursive,
        vertical_only=args.vertical_only,
        full_only=args.full_only,
        bins_only=args.bins_only,
        version=args.version,
    )  # returns 0 or None


def _run_files(args: argparse.Namespace) -> CommandResult:
    files_command(name=args.files)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(_normalize_legacy_argv(list(sys.argv[1:] if argv is None else argv)))
    if args.install:
        return install()
    if args.uninstall:
        return uninstall()
    if args.files is not False:
        result = _run_files(args)
    else:
        result = _run_create_bins(args)
    if result is None:
        return 0
    return int(result)


if __name__ == "__main__":
    raise SystemExit(main())

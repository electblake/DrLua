"""Desktop entry point for the DrLua Qt Widgets application."""

from drlua.ui.application import run_application


def main() -> int:
    return run_application()


if __name__ == "__main__":
    raise SystemExit(main())

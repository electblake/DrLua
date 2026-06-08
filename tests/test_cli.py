from __future__ import annotations

from typer.testing import CliRunner

from drlua.cli import app


runner = CliRunner()


def test_root_help_lists_create_bins_command() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "create-bins" in result.stdout
    assert "organize-media-bin" in result.stdout


def test_create_bins_help_shows_expected_options() -> None:
    result = runner.invoke(app, ["create-bins", "--help"])

    assert result.exit_code == 0
    assert "Usage:" in result.stdout
    assert "INPUT_FOLDER" in result.stdout
    assert "--name" in result.stdout
    assert "--section" in result.stdout
    assert "--recursive" in result.stdout
    assert "--only-bins" in result.stdout or "--timeline" in result.stdout

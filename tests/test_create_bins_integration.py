from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from drlua import create_bins as create_bins_module


@pytest.mark.skipif(shutil.which("ffprobe") is None, reason="ffprobe is required for media metadata probing")
def test_create_bins_with_sample_videos(tmp_path: Path, capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch) -> None:
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    assert sample_dir.is_dir()

    monkeypatch.setattr(create_bins_module, "PROCESSED_DATA_DIR", tmp_path / "processed")

    result = create_bins_module.create_bins(
        sample_dir,
        name="Sample",
        section="Fansites",
        tag=["integration"],
        vertical_only=True,
    )

    assert result is None

    generated_files = list((tmp_path / "processed" / "create_bins").glob("*.lua"))
    assert len(generated_files) == 1

    generated_lua = generated_files[0].read_text(encoding="utf-8")
    assert "CreateBins(" in generated_lua
    assert "Sample" in generated_lua
    assert "data\\sample" in generated_lua or "data/sample" in generated_lua
    assert "laryn18xxx-2021-06-02-0gr4lzs9.mp4" in generated_lua

    output = capsys.readouterr().out
    assert "Paste into the DaVinci Resolve Lua console" in output
    assert f"dofile([[{generated_files[0].resolve().as_posix()}]])" in output

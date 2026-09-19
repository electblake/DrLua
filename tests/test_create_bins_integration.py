from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from loguru import logger

from drlua import create_bins as create_bins_module


@pytest.mark.skipif(shutil.which("ffprobe") is None, reason="ffprobe is required for media metadata probing")
def test_create_bins_with_sample_videos(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    sample_dir = Path(__file__).resolve().parents[1] / "data" / "sample"
    assert sample_dir.is_dir()

    monkeypatch.setattr(create_bins_module, "PROCESSED_DATA_DIR", tmp_path / "processed")

    log_path = tmp_path / "generation.log"
    sink = logger.add(log_path, catch=False)
    progress = []
    result = create_bins_module.create_bins(
        [sample_dir],
        name="Sample",
        section="Fansites",
        tag=["integration"],
        vertical_only=True,
        progress=lambda *event: progress.append(event),
    )

    logger.remove(sink)
    assert result is None
    assert progress[0] == ("Scanning sources", 0, 1)
    probing = [event for event in progress if event[0] == "Probing media"]
    total = probing[0][2]
    assert [event[1] for event in probing] == list(range(total + 1))
    assert progress[-3:] == [
        ("Grouping clips", total, total),
        ("Writing Lua script", total, total),
        ("Complete", total, total),
    ]

    generated_files = list((tmp_path / "processed" / "create_bins").glob("*.lua"))
    assert len(generated_files) == 1

    generated_lua = generated_files[0].read_text(encoding="utf-8")
    assert "CreateBins(" in generated_lua
    assert "Sample" in generated_lua
    assert "data\\sample" in generated_lua or "data/sample" in generated_lua
    assert "laryn18xxx-2021-06-02-0gr4lzs9.mp4" in generated_lua

    output = log_path.read_text(encoding="utf-8")
    assert "Paste into the DaVinci Resolve Lua console" in output
    assert f"dofile([[{generated_files[0].resolve().as_posix()}]])" in output

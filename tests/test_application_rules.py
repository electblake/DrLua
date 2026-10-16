from pathlib import Path

import pytest

from drlua.application.generation import GenerationRequest, split_sources, split_tags
from drlua.application.progress import Progress


def test_text_parsing():
    assert split_sources(" a | b\r\nc \n") == ["a", "b", "c"]
    assert split_tags(" a, b\nc,, ") == ["a", "b", "c"]


def test_progress_rate_eta_and_finalization():
    progress = Progress(total=1)
    assert "Scanning sources: 0/1" in progress.status(99)
    progress.update("Probing media", 0, 10, 100)
    assert "ETA —" in progress.status(100)
    progress.update("Probing media", 4, 10, 102)
    assert progress.value == 4 and progress.maximum == 12
    assert "2.00 items/s  |  ETA 0:03" in progress.status(102)
    assert "1.00 items/s  |  ETA 0:06" in progress.status(104)
    progress.update("Probing media", 10, 10, 105)
    progress.update("Grouping clips", 10, 10, 106)
    assert "finalizing" in progress.status(106)
    progress.update("Writing Lua script", 10, 10, 107)
    assert progress.value == 11
    progress.update("Complete", 10, 10, 108)
    assert progress.value == progress.maximum
    assert "Lua script created: 10/10 items" in progress.status(108)
    assert "2.00 items/s  |  ETA 0:00" in progress.status(108)


def test_generation_failure_is_not_wrapped(monkeypatch):
    from drlua.application import generation

    def fail(*args, **kwargs):
        raise RuntimeError("generation failed")

    monkeypatch.setattr(generation, "create_bins", fail)
    with pytest.raises(RuntimeError, match="generation failed"):
        GenerationRequest((Path("source"),), "name", "section", "", ()).execute(
            lambda *args: None
        )

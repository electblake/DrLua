from io import BytesIO

import pytest

from drlua import updates


def test_release_versions_compare_numerically():
    assert updates.version_tuple("v0.10.0") > updates.version_tuple("0.9.9")


def test_download_selects_setup_and_keeps_downloads_separate(monkeypatch, tmp_path):
    monkeypatch.setattr(updates.tempfile, "tempdir", str(tmp_path))
    requests = []

    def download(request, **kwargs):
        requests.append(request.full_url)
        return BytesIO(b"installer contents")

    monkeypatch.setattr(updates, "urlopen", download)
    release = {"tag_name": "v0.3.0", "assets": [
        {"name": "DrLua-0.3.0-windows-amd64.zip"},
        {"name": "DrLua-0.3.0-windows-amd64-Setup.exe", "browser_download_url": "https://example.test/setup"},
    ]}
    first = updates.download_setup(release)
    second = updates.download_setup(release)
    assert first != second
    assert first.read_bytes() == second.read_bytes() == b"installer contents"
    assert requests == ["https://example.test/setup"] * 2


def test_missing_installer_surfaces():
    with pytest.raises(StopIteration):
        updates.download_setup({"tag_name": "v0.3.0", "assets": []})

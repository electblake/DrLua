from io import BytesIO
import json

import pytest

from drlua import __version__, updates


@pytest.mark.parametrize("latest, installed, newer", [
    ("0.10.0", "0.9.9", True),
    ("1.0.0", "1.0.0", False),
    ("0.9.9", "0.10.0", False),
])
def test_release_versions_compare_numerically(latest, installed, newer):
    assert (updates.version_tuple(latest) > updates.version_tuple(installed)) is newer


def test_latest_release_request(monkeypatch):
    def fetch(request, timeout):
        assert request.full_url == "https://api.github.com/repos/electblake/DrLua/releases/latest"
        headers = dict((k.lower(), v) for k, v in request.header_items())
        assert headers == {
            "accept": "application/vnd.github+json",
            "user-agent": f"DrLua/{__version__}",
            "x-github-api-version": updates.GITHUB_API_VERSION,
        }
        assert timeout == 30
        return BytesIO(json.dumps({"tag_name": "v1.0.0"}).encode())

    monkeypatch.setattr(updates, "urlopen", fetch)
    assert updates.latest_release() == {"tag_name": "v1.0.0"}


def test_download_selects_exact_platform_setup_and_reports_chunks(monkeypatch, tmp_path):
    monkeypatch.setattr(updates.platform, "system", lambda: "Windows")
    monkeypatch.setattr(updates.platform, "machine", lambda: "AMD64")
    def cache(name, appauthor):
        assert name == "DrLua" and appauthor is False
        return tmp_path
    monkeypatch.setattr(updates, "user_cache_path", cache)
    contents = b"x" * (256 * 1024 * 2 + 11)
    requests = []

    class Response(BytesIO):
        def read(self, size):
            assert size == 256 * 1024
            return super().read(size)

    def download(request, timeout):
        requests.append(request.full_url)
        assert timeout == 30
        return Response(contents)

    monkeypatch.setattr(updates, "urlopen", download)
    release = {"tag_name": "v0.3.0", "assets": [
        {"name": "DrLua-0.3.0-windows-amd64.zip"},
        {"name": "DrLua-0.3.0-windows-arm64-Setup.exe"},
        {"name": "DrLua-0.3.0-windows-amd64-Setup.exe",
         "browser_download_url": "https://example.test/setup", "size": len(contents)},
    ]}
    progress = []
    path = updates.download_setup(release, lambda current, total: progress.append((current, total)))
    assert path == tmp_path / "updates" / "DrLua-0.3.0-windows-amd64-Setup.exe"
    assert path.read_bytes() == contents
    assert progress == [(256 * 1024, len(contents)), (512 * 1024, len(contents)), (len(contents), len(contents))]
    assert requests == ["https://example.test/setup"]


def test_missing_installer_surfaces():
    with pytest.raises(StopIteration):
        updates.download_setup({"tag_name": "v0.3.0", "assets": []}, lambda *args: None)

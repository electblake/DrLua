import json
from pathlib import Path
import shutil
import tempfile
from urllib.request import Request, urlopen

from drlua import __version__


def latest_release() -> dict:
    request = Request(
        "https://api.github.com/repos/electblake/DrLua/releases/latest",
        headers={"Accept": "application/vnd.github+json", "User-Agent": f"DrLua/{__version__}"},
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def version_tuple(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.removeprefix("v").split("."))


def download_setup(release: dict) -> Path:
    version = release["tag_name"].removeprefix("v")
    name = f"DrLua-{version}-windows-amd64-Setup.exe"
    asset = next(asset for asset in release["assets"] if asset["name"] == name)
    setup_path = Path(tempfile.mkdtemp(prefix="DrLua-update-")) / name
    request = Request(asset["browser_download_url"], headers={"User-Agent": f"DrLua/{__version__}"})
    with urlopen(request, timeout=30) as response, setup_path.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    return setup_path

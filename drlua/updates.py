import json
import platform
from urllib.request import Request, urlopen

from platformdirs import user_cache_path

from drlua import __version__
from drlua.integrations import APP_NAME

GITHUB_REPOSITORY = "electblake/DrLua"
GITHUB_API_VERSION = "2022-11-28"
RELEASES_URL = f"https://github.com/{GITHUB_REPOSITORY}/releases"


def latest_release() -> dict:
    request = Request(
        f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": f"{APP_NAME}/{__version__}",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        },
    )
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def version_tuple(value: str) -> tuple[int, ...]:
    return tuple(int(part) for part in value.split("."))


def download_setup(release: dict, report_progress):
    version = release["tag_name"].removeprefix("v")
    name = (
        f"{APP_NAME}-{version}-{platform.system().lower()}-"
        f"{platform.machine().lower()}-Setup.exe"
    )
    asset = next(asset for asset in release["assets"] if asset["name"] == name)
    directory = user_cache_path(APP_NAME, appauthor=False) / "updates"
    directory.mkdir(parents=True, exist_ok=True)
    setup_path = directory / name
    request = Request(asset["browser_download_url"], headers={"User-Agent": f"{APP_NAME}/{__version__}"})
    current = 0
    with urlopen(request, timeout=30) as response, setup_path.open("wb") as stream:
        while chunk := response.read(256 * 1024):
            stream.write(chunk)
            current += len(chunk)
            report_progress(current, asset["size"])
    return setup_path

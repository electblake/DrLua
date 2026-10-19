"""User preferences and isolated storage for a no-profile desktop session."""

from pathlib import Path
import sys
import tempfile

from platformdirs import PlatformDirs
from PySide6.QtCore import QSettings


class Profile:
    def __init__(self, no_profile=False):
        self.no_profile = no_profile
        if no_profile:
            self.root = Path(tempfile.mkdtemp(prefix="DrLua-no-profile-"))
            self.config_path = self.root / "config"
            self.data_path = self.root / "data"
            self.log_path = self.root / "logs"
            self.settings = None
            self.save_directory = self.data_path / "processed" / "create_bins"
            self.recursive = True
        else:
            dirs = PlatformDirs("DrLua", "DrLua")
            self.config_path = dirs.user_config_path
            self.data_path = dirs.user_data_path
            self.log_path = dirs.user_log_path
            self.settings = QSettings("DrLua", "DrLua")
            self.recursive = self.settings.value("recursive", True, type=bool)
            self.save_directory = Path(self.settings.value(
                "saveDirectory", str(self.data_path / "processed" / "create_bins"), type=str
            ))

    def set_recursive(self, recursive: bool):
        self.recursive = recursive
        if self.settings is not None:
            self.settings.setValue("recursive", recursive)
            self.settings.sync()

    def set_save_directory(self, directory: str):
        self.save_directory = Path(directory).expanduser().resolve()
        if self.settings is not None:
            self.settings.setValue("saveDirectory", str(self.save_directory))
            self.settings.sync()


profile = Profile(no_profile="-NoProfile" in sys.argv[1:])

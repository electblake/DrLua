from pathlib import Path
import json
import subprocess
import sys

from PySide6.QtCore import QSettings

from drlua import profile as profile_module
from drlua.profile import Profile


def test_default_save_directory_and_qsettings_restart(monkeypatch, tmp_path):
    settings_file = tmp_path / "preferences.ini"
    monkeypatch.setattr(profile_module, "QSettings", lambda *args: QSettings(str(settings_file), QSettings.Format.IniFormat))
    first = Profile()
    assert first.save_directory == first.data_path / "processed" / "create_bins"
    chosen = tmp_path / "my scripts"
    first.set_save_directory(str(chosen))
    second = Profile()
    assert second.save_directory == chosen
    assert QSettings(str(settings_file), QSettings.Format.IniFormat).value("saveDirectory") == str(chosen)
    before = settings_file.read_bytes()
    isolated = Profile(no_profile=True)
    assert isolated.settings is None
    assert isolated.save_directory.is_relative_to(isolated.root)
    isolated.set_save_directory(str(tmp_path / "session output"))
    assert settings_file.read_bytes() == before
    assert Profile().save_directory == chosen


def test_no_profile_startup_never_opens_user_settings_or_paths():
    script = '''
import json
import sys
import platformdirs
from PySide6 import QtCore

def forbidden(*args, **kwargs):
    raise AssertionError("No-profile startup accessed persistent user storage")

QtCore.QSettings = forbidden
platformdirs.PlatformDirs = forbidden
from drlua import config
from drlua.ui.window import MainWindow
from drlua.ui.controller import AppController
from PySide6.QtWidgets import QApplication
app = QApplication([])
controller = AppController()
window = MainWindow(controller)
assert controller.profile.no_profile
assert controller.profile.settings is None
assert config.PROJ_ROOT.is_relative_to(controller.profile.root)
assert config.DATA_DIR.is_relative_to(controller.profile.root)
assert config.LOG_PATH.is_relative_to(controller.profile.root)
assert config.LOG_PATH.exists()
assert (config.LUA_DIR / "lib.lua").exists()
controller.shutdown()
print(json.dumps({"root": str(controller.profile.root), "save": controller.saveDirectory}))
'''
    result = subprocess.run([sys.executable, "-c", script, "-NoProfile"], text=True, capture_output=True, check=True)
    paths = json.loads(result.stdout)
    assert Path(paths["save"]).is_relative_to(Path(paths["root"]))

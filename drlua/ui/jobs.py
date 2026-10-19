"""Blocking application operations run in QThreads; only signals cross to the UI."""

from collections.abc import Callable
from pathlib import Path
import time

from PySide6.QtCore import QThread, Signal
from loguru import logger

from drlua.application.generation import GenerationRequest


class MetadataJob(QThread):
    resultReady = Signal(object)

    def __init__(self, operation: Callable, *args, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.args = args
        self.cancelled = False

    def cancel(self):
        self.cancelled = True
        self.requestInterruption()

    def run(self):
        result = self.operation(*self.args)
        if not self.cancelled:
            self.resultReady.emit(result)


class FilesJob(QThread):
    resultReady = Signal(object, object)

    def __init__(self, directory: Path, parent=None):
        super().__init__(parent)
        self.directory = directory

    def run(self) -> None:
        self.directory.mkdir(parents=True, exist_ok=True)
        paths = sorted(
            (path for path in self.directory.iterdir()
             if path.is_file() and path.suffix.lower() == ".lua"),
            key=lambda path: path.name.casefold(),
        )
        self.resultReady.emit(self.directory, paths)


class DeleteFilesJob(QThread):
    resultReady = Signal(object)

    def __init__(self, paths, parent=None):
        super().__init__(parent)
        self.paths = paths

    def run(self):
        for path in self.paths:
            path.unlink()
        self.resultReady.emit(self.paths)


class RenameFileJob(QThread):
    resultReady = Signal(object)

    def __init__(self, path, filename, parent=None):
        super().__init__(parent)
        self.path = path
        self.filename = filename

    def run(self):
        path = self.path.rename(self.path.with_name(self.filename))
        self.resultReady.emit(path)


class GenerationJob(QThread):
    progress = Signal(str, int, int, float)
    resultReady = Signal(object)
    activity = Signal(str)

    def __init__(self, request: GenerationRequest, parent=None):
        super().__init__(parent)
        self.request = request

    def run(self) -> None:
        result = self.request.execute(self.report_progress, self.report_activity)
        if result is not None:
            self.resultReady.emit(result)

    def report_activity(self, message):
        self.activity.emit(message)
        logger.info(message)

    def report_progress(self, stage: str, completed: int, total: int) -> None:
        self.progress.emit(stage, completed, total, time.perf_counter())


class UpdateJob(QThread):
    resultReady = Signal(object)

    def __init__(self, operation: Callable, *args, parent=None):
        super().__init__(parent)
        self.operation = operation
        self.args = args

    def run(self) -> None:
        self.resultReady.emit(self.operation(*self.args))


class DownloadUpdateJob(QThread):
    resultReady = Signal(object)
    progress = Signal(object, object)

    def __init__(self, release, parent=None):
        super().__init__(parent)
        self.release = release

    def run(self):
        from drlua.updates import download_setup

        self.resultReady.emit(download_setup(self.release, self.progress.emit))

"""Blocking application operations run in QThreads; only signals cross to the UI."""

from collections.abc import Callable
import time

from PySide6.QtCore import QThread, Signal

from drlua.application.generation import GenerationRequest


class GenerationJob(QThread):
    progress = Signal(str, int, int, float)

    def __init__(self, request: GenerationRequest, parent=None):
        super().__init__(parent)
        self.request = request

    def run(self) -> None:
        self.request.execute(self.report_progress)

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

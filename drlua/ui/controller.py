from pathlib import Path
import time

from loguru import logger
from PySide6.QtCore import QObject, Property, QTimer, QUrl, Signal, Slot, Qt
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtQml import QmlElement, QmlUncreatable

from drlua import __version__, updates
from drlua.application.generation import split_sources
from drlua.application.progress import Progress
from drlua.config import PROCESSED_DATA_DIR
from drlua.ui.form import FormModel
from drlua.ui.jobs import GenerationJob, UpdateJob

QML_IMPORT_NAME = "DrLua"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
@QmlUncreatable("Created at application startup")
class AppController(QObject):
    busyChanged = Signal()
    statusChanged = Signal()
    progressChanged = Signal()
    canGenerateChanged = Signal()
    outputAppended = Signal(str)
    updateAvailable = Signal(str)
    installReady = Signal()
    logReceived = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._form = FormModel(self)
        self._busy = False
        self._status = "Choose source folders or files to get started."
        self._progress = Progress()
        self._output = []
        self._jobs = []
        self.setup_path: Path | None = None
        self._release = None
        self._form.sourcesChanged.connect(self.canGenerateChanged)
        self.busyChanged.connect(self.canGenerateChanged)
        self._metrics = QTimer(self)
        self._metrics.setInterval(100)
        self._metrics.timeout.connect(self.refreshMetrics)
        self.logReceived.connect(self.appendLog, Qt.ConnectionType.QueuedConnection)
        self._sink = logger.add(
            self.receive_log,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}",
            colorize=False,
            catch=False,
        )

    @Property(FormModel, constant=True)
    def form(self):
        return self._form

    @Property(str, constant=True)
    def version(self):
        return __version__

    @Property(bool, notify=busyChanged)
    def busy(self):
        return self._busy

    @Property(bool, notify=canGenerateChanged)
    def canGenerate(self):
        return bool(split_sources(self._form.sources)) and not self._busy

    @Property(str, notify=statusChanged)
    def status(self):
        return self._status

    @Property(int, notify=progressChanged)
    def progressValue(self):
        return self._progress.value

    @Property(int, notify=progressChanged)
    def progressMaximum(self):
        return self._progress.maximum

    def set_status(self, value):
        self._status = value
        self.statusChanged.emit()

    def set_busy(self, value):
        self._busy = value
        self.busyChanged.emit()

    def start_job(self, job):
        self._jobs.append(job)
        job.finished.connect(self.jobFinished)
        job.finished.connect(job.deleteLater)
        job.start()

    @Slot()
    def jobFinished(self):
        self._jobs.remove(self.sender())

    @Slot()
    def generate(self):
        request = self._form.snapshot()
        self.set_busy(True)
        self._progress = Progress(total=len(request.sources))
        self.refreshMetrics()
        job = GenerationJob(request, self)
        job.progress.connect(self.receiveProgress)
        job.finished.connect(self.generationFinished)
        self._metrics.start()
        self.start_job(job)

    @Slot(str, int, int, float)
    def receiveProgress(self, stage, completed, total, timestamp):
        self._progress.update(stage, completed, total, timestamp)
        self.refreshMetrics()

    @Slot()
    def refreshMetrics(self):
        self.set_status(self._progress.status(time.perf_counter()))
        self.progressChanged.emit()

    @Slot()
    def generationFinished(self):
        self._metrics.stop()
        self.set_busy(False)

    def receive_log(self, message):
        self.logReceived.emit(str(message))

    @Slot(str)
    def appendLog(self, message):
        self._output.append(message)
        self.outputAppended.emit(message)

    @Slot()
    def copyOutput(self):
        QGuiApplication.clipboard().setText("".join(self._output))

    @Slot()
    def openOutput(self):
        folder = PROCESSED_DATA_DIR / "create_bins"
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    @Slot()
    def checkUpdates(self):
        self.set_busy(True)
        self.set_status("Checking for updates…")
        job = UpdateJob(updates.latest_release, parent=self)
        job.resultReady.connect(self.releaseReceived)
        self.start_job(job)

    @Slot(object)
    def releaseReceived(self, release):
        self._release = release
        if updates.version_tuple(release["tag_name"]) > updates.version_tuple(
            __version__
        ):
            self.updateAvailable.emit(release["tag_name"])
        else:
            self.set_status(f"DrLua {__version__} is up to date.")
            self.set_busy(False)

    @Slot()
    def declineUpdate(self):
        self.set_status("Update cancelled.")
        self.set_busy(False)

    @Slot()
    def acceptUpdate(self):
        self.set_status("Downloading update…")
        job = UpdateJob(updates.download_setup, self._release, parent=self)
        job.resultReady.connect(self.downloadReceived)
        self.start_job(job)

    @Slot(object)
    def downloadReceived(self, path):
        self.setup_path = path
        self.installReady.emit()

    @Slot()
    def shutdown(self):
        self._metrics.stop()
        for job in self._jobs:
            job.wait()
        logger.remove(self._sink)

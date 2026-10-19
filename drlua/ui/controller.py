from pathlib import Path
from dataclasses import replace
import traceback
import time

from loguru import logger
from PySide6.QtCore import QObject, Property, QThread, QTimer, QUrl, Signal, Slot, Qt
from PySide6.QtGui import QDesktopServices, QGuiApplication

from drlua import __version__, updates
from drlua.application import catalog
from drlua.application.generation import split_sources
from drlua.application.progress import Progress
from drlua.profile import profile
from drlua.ui.form import FormModel
from drlua.ui.jobs import FilesJob, GenerationJob, UpdateJob


class AppController(QObject):
    busyChanged = Signal()
    statusChanged = Signal()
    progressChanged = Signal()
    canGenerateChanged = Signal()
    outputAppended = Signal(str)
    updateAvailable = Signal(str)
    installReady = Signal()
    logReceived = Signal(str)
    saveDirectoryChanged = Signal()
    filesListed = Signal(object, object)
    generatedCommandChanged = Signal()
    exceptionReceived = Signal(object, str)

    def __init__(self, parent=None, user_profile=profile):
        super().__init__(parent)
        self.profile = user_profile
        self._form = FormModel(self)
        self._form.recursive = self.profile.recursive
        self._form.recursiveChanged.connect(lambda: self.profile.set_recursive(self._form.recursive))
        self._busy = False
        self._status = "Choose source folders or files to get started."
        self._progress = Progress()
        self._output = []
        self._generated_command = ""
        self._jobs = []
        self._pending_request = None
        self._pending_job = None
        self._active_job = None
        self._generating = False
        self._cancelling = False
        self._activity = ""
        self._started_at = 0
        self.setup_path: Path | None = None
        self._release = None
        self._form.sourcesChanged.connect(self.canGenerateChanged)
        self.busyChanged.connect(self.canGenerateChanged)
        self._form.inferenceFinished.connect(self.sourcePrepared)
        self.exceptionReceived.connect(self.showException, Qt.ConnectionType.QueuedConnection)
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

    @Property(bool, notify=busyChanged)
    def canCancel(self):
        return self._generating and not self._cancelling

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
        self._generating = True
        self._cancelling = False
        self._generated_command = ""
        self.generatedCommandChanged.emit()
        self.set_busy(True)
        self._started_at = time.perf_counter()
        self._activity = "Starting generation"
        self._progress = Progress(stage="Preparing sources")
        self.refreshMetrics()
        self._metrics.start()
        if not self._form.name.strip():
            self._form.inferSource()
        request = self._form.snapshot(self.profile.save_directory)
        self.appendLog("Starting generation.\n")
        self.appendLog(f"Source paths: {self._form.sources}\n")
        if self._form.inferencePending:
            self._pending_request = request
            self._pending_job = self._form.inferenceJob
            self._activity = "Preparing source metadata…"
            self.refreshMetrics()
            self.appendLog("Preparing source metadata…\n")
        else:
            self.startGeneration(request)

    @Slot()
    def cancelGeneration(self):
        self._cancelling = True
        self._pending_request = None
        if self._pending_job is not None:
            self._form.cancelInference(self._pending_job)
            self._pending_job = None
            self.finishCancellation()
            return
        self._active_job.requestInterruption()
        self._metrics.stop()
        self.set_status("Cancelling…")
        self.busyChanged.emit()

    @Slot(object, object)
    def sourcePrepared(self, job, result):
        source, name, (section, category) = result
        if self._pending_request is not None and job is self._pending_job:
            request = self._pending_request
            self._pending_request = None
            self._pending_job = None
            if not request.name:
                request = replace(request, name=name, section=section or request.section,
                                  tags=request.tags or tuple(catalog.category_tags(section, category)))
            self.startGeneration(request)

    def startGeneration(self, request):
        self._progress = Progress(total=len(request.sources))
        self.refreshMetrics()
        job = GenerationJob(request, self)
        self._active_job = job
        job.progress.connect(self.receiveProgress)
        job.activity.connect(self.receiveActivity)
        job.resultReady.connect(self.generationResult)
        job.finished.connect(self.generationFinished)
        self._metrics.start()
        self.start_job(job)

    def reportException(self, exception_type, exception, tb):
        self.exceptionReceived.emit(QThread.currentThread(), "".join(traceback.format_exception(exception_type, exception, tb)))

    @Slot(object, str)
    def showException(self, job, message):
        self.appendLog(message)
        self.set_status(f"Failed: {message.rstrip().splitlines()[-1]}")
        if job is self._pending_job or job is self._active_job:
            self._generating = False
            self._pending_request = None
            self._pending_job = None
            self._active_job = None
            self._metrics.stop()
            self.set_busy(False)

    @Property(str, notify=generatedCommandChanged)
    def generatedCommand(self):
        return self._generated_command

    @Slot(object)
    def generationResult(self, path):
        if self.sender() is not None and self.sender() is not self._active_job:
            return
        self._cancelling = False
        self._generating = False
        filename = path.as_posix()
        equals = ""
        while f"]{equals}]" in filename:
            equals += "="
        self._generated_command = f"dofile([{equals}[{filename}]{equals}])"
        self.generatedCommandChanged.emit()
        self._activity = f"Saved Lua script: {filename}"
        self.refreshMetrics()

    @Slot()
    def copyGeneratedCommand(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self._generated_command)
        if clipboard.text() == self._generated_command:
            self.set_status("Copied 1 command to clipboard.")
        else:
            self.set_status("Failed to copy 1 command to clipboard.")

    @Slot(str, int, int, float)
    def receiveProgress(self, stage, completed, total, timestamp):
        if self.sender() is not self._active_job:
            return
        self._progress.update(stage, completed, total, timestamp)
        if not self._cancelling:
            self.refreshMetrics()

    @Slot(str)
    def receiveActivity(self, message):
        if self._cancelling or self.sender() is not self._active_job:
            return
        self._activity = message
        self.refreshMetrics()

    @Slot()
    def refreshMetrics(self):
        now = time.perf_counter()
        elapsed = int(now - self._started_at)
        self.set_status(f"{self._progress.status(now)}  |  Elapsed {elapsed // 60}:{elapsed % 60:02d}\n{self._activity}")
        self.progressChanged.emit()

    @Slot()
    def generationFinished(self):
        if self.sender() is not self._active_job:
            return
        self._metrics.stop()
        self._generating = False
        self._active_job = None
        if self._cancelling:
            self.finishCancellation()
        else:
            self.set_busy(False)

    def finishCancellation(self):
        self._metrics.stop()
        self._active_job = None
        self._generating = False
        self._cancelling = False
        self._generated_command = ""
        self.generatedCommandChanged.emit()
        self._progress = Progress(stage="Cancelled")
        self.progressChanged.emit()
        self.set_status("Generation cancelled.")
        self.appendLog("Generation cancelled.\n")
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
        folder = self.profile.save_directory
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    @Slot()
    def listFiles(self):
        job = FilesJob(self.profile.save_directory, self)
        job.resultReady.connect(self.filesListed)
        self.start_job(job)

    @Property(str, notify=saveDirectoryChanged)
    def saveDirectory(self):
        return str(self.profile.save_directory)

    @saveDirectory.setter
    def saveDirectory(self, directory):
        self.profile.set_save_directory(directory)
        self.saveDirectoryChanged.emit()

    @Slot()
    def checkUpdates(self):
        self.set_busy(True)
        self.set_status("Checking for updates…")
        job = UpdateJob(updates.latest_release, parent=self)
        self._active_job = job
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
        self._active_job = job
        job.resultReady.connect(self.downloadReceived)
        self.start_job(job)

    @Slot(object)
    def downloadReceived(self, path):
        self.setup_path = path
        self.installReady.emit()

    @Slot()
    def shutdown(self):
        self._pending_request = None
        self._pending_job = None
        self._metrics.stop()
        self._form.shutdown()
        for job in self._jobs:
            job.wait()
        logger.remove(self._sink)

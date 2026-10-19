from pathlib import Path

from PySide6.QtCore import QObject, Property, QThread, Signal, Slot

from drlua.application import catalog
from drlua.application.generation import (
    GenerationRequest,
    default_name,
    split_sources,
    split_tags,
)
from drlua.ui.jobs import MetadataJob


def source_metadata(source):
    name = default_name(source)
    if QThread.currentThread().isInterruptionRequested():
        return
    return source, name


class FormModel(QObject):
    sourcesChanged = Signal()
    recursiveChanged = Signal()
    nameChanged = Signal()
    sectionChanged = Signal()
    categoryChanged = Signal()
    groupChanged = Signal()
    tagsChanged = Signal()
    categoriesChanged = Signal()
    inferenceFinished = Signal(object, object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sources = ""
        self._recursive = True
        self._name = ""
        self._section = catalog.section_options()[0]
        self._category = ""
        self._group = ""
        self._tags = ""
        self._categories = catalog.category_options(self._section)
        self._jobs = []
        self._inference_source = None
        self.inferenceJob = None
        self._inferred_source = None

    def start_job(self, job):
        self._jobs.append(job)
        job.finished.connect(self.jobFinished)
        job.finished.connect(job.deleteLater)
        job.start()

    @Slot()
    def jobFinished(self):
        if self.sender() is self.inferenceJob:
            self._inference_source = None
            self.inferenceJob = None
        self._jobs.remove(self.sender())

    @Property(str, notify=sourcesChanged)
    def sources(self):
        return self._sources

    @sources.setter
    def sources(self, value):
        if self._sources != value:
            self._sources = value
            self.sourcesChanged.emit()

    @Property(bool, notify=recursiveChanged)
    def recursive(self):
        return self._recursive

    @recursive.setter
    def recursive(self, value):
        if self._recursive != value:
            self._recursive = value
            self.recursiveChanged.emit()

    @Property(str, notify=nameChanged)
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if self._name != value:
            self._name = value
            self.nameChanged.emit()

    @Property(str, notify=sectionChanged)
    def section(self):
        return self._section

    @section.setter
    def section(self, value):
        if self._section != value:
            self._section = value
            self._categories = catalog.category_options(value)
            self.category = ""
            self.tags = ""
            self.categoriesChanged.emit()
            self.sectionChanged.emit()

    @Property(str, notify=categoryChanged)
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if self._category != value:
            self._category = value
            self.categoryChanged.emit()
            self.tags = value.strip()

    @Property(str, notify=groupChanged)
    def group(self):
        return self._group

    @group.setter
    def group(self, value):
        if self._group != value:
            self._group = value
            self.groupChanged.emit()

    @Property(str, notify=tagsChanged)
    def tags(self):
        return self._tags

    @tags.setter
    def tags(self, value):
        if self._tags != value:
            self._tags = value
            self.tagsChanged.emit()

    @Property("QStringList", constant=True)
    def sections(self):
        return catalog.section_options()

    @Property("QStringList", notify=categoriesChanged)
    def categories(self):
        return self._categories

    @Slot()
    def inferSource(self):
        paths = split_sources(self._sources)
        if paths:
            if paths[0] == self._inference_source:
                return
            if paths[0] == self._inferred_source and self._name.strip():
                return
            self._inference_source = paths[0]
            job = MetadataJob(source_metadata, paths[0], parent=self)
            self.inferenceJob = job
            job.resultReady.connect(self.sourceReceived)
            self.start_job(job)

    @Slot(object)
    def sourceReceived(self, result):
        job = self.sender()
        if job.cancelled:
            return
        source, name = result
        if job is self.inferenceJob and split_sources(self._sources)[:1] == [source]:
            if not self._name.strip():
                self.name = name
            self._inferred_source = source
        if self.sender() is self.inferenceJob:
            self._inference_source = None
        self.inferenceFinished.emit(job, result)

    def cancelInference(self, job):
        job.cancel()
        if job is self.inferenceJob:
            self.inferenceJob = None
            self._inference_source = None

    @property
    def inferencePending(self):
        return self._inference_source is not None and split_sources(self._sources)[:1] == [self._inference_source]

    def shutdown(self):
        for job in self._jobs:
            job.wait()

    @Slot("QVariantList")
    def appendUrls(self, urls):
        self.sources = "\n".join(
            filter(None, [self._sources.strip(), *(url.toLocalFile() for url in urls)])
        )
        self.inferSource()

    def snapshot(self, output_directory: Path) -> GenerationRequest:
        return GenerationRequest(
            tuple(Path(value) for value in split_sources(self._sources)),
            self._name.strip(),
            self._section.strip(),
            self._group.strip(),
            tuple(split_tags(self._tags)),
            output_directory,
            recursive=self._recursive,
        )

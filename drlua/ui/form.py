from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtQml import QmlElement, QmlUncreatable

from drlua.application import catalog
from drlua.application.generation import (
    GenerationRequest,
    default_name,
    split_sources,
    split_tags,
)

QML_IMPORT_NAME = "DrLua"
QML_IMPORT_MAJOR_VERSION = 1


@QmlElement
@QmlUncreatable("Owned by the application controller")
class FormModel(QObject):
    sourcesChanged = Signal()
    nameChanged = Signal()
    sectionChanged = Signal()
    categoryChanged = Signal()
    groupChanged = Signal()
    tagsChanged = Signal()
    categoriesChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._sources = ""
        self._name = ""
        self._section = catalog.section_options()[0]
        self._category = ""
        self._group = ""
        self._tags = ""
        self._categories = catalog.category_options(self._section)

    @Property(str, notify=sourcesChanged)
    def sources(self):
        return self._sources

    @sources.setter
    def sources(self, value):
        if self._sources != value:
            self._sources = value
            self.sourcesChanged.emit()

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
            self._categories = catalog.category_options(value.strip())
            self.categoriesChanged.emit()
            self.sectionChanged.emit()
            self.category = ""
            self.tags = ""

    @Property(str, notify=categoryChanged)
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        if self._category != value:
            self._category = value
            self.categoryChanged.emit()
            self.tags = "\n".join(
                catalog.category_tags(self._section.strip(), value.strip())
            )

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
            if not self._name.strip():
                self.name = default_name(paths[0])
            section, category = catalog.match_section_category(paths[0])
            if section:
                self.section = section
                self.category = category or ""

    @Slot("QVariantList")
    def appendUrls(self, urls):
        self.sources = "\n".join(
            filter(None, [self._sources.strip(), *(url.toLocalFile() for url in urls)])
        )
        self.inferSource()

    def snapshot(self) -> GenerationRequest:
        return GenerationRequest(
            tuple(Path(value) for value in split_sources(self._sources)),
            self._name.strip(),
            self._section.strip(),
            self._group.strip(),
            tuple(split_tags(self._tags)),
        )

"""Desktop presentation using unmodified Qt Widgets and platform defaults."""

from pathlib import Path

from PySide6.QtCore import QEvent, QSignalBlocker, QUrl, Qt
from PySide6.QtGui import QAction, QContextMenuEvent, QKeySequence, QTextCursor
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMenu, QMessageBox, QPlainTextEdit,
    QListWidget, QListWidgetItem, QProgressBar, QPushButton, QScrollArea, QSplitter, QTabWidget,
    QVBoxLayout, QWidget,
)

from drlua.ui.controller import AppController


class SourceEditor(QPlainTextEdit):
    def insertFromMimeData(self, source):
        if source.hasUrls():
            self.insertPlainText("\n".join(url.toLocalFile() for url in source.urls()))
        else:
            super().insertFromMimeData(source)


class SavedFilesList(QListWidget):
    def contextMenuEvent(self, event):
        if event.reason() == QContextMenuEvent.Reason.Keyboard:
            item = self.currentItem()
        else:
            item = self.itemAt(event.pos())
        if item is None or item.isHidden():
            return
        if not item.isSelected():
            self.setCurrentItem(item)
        position = event.globalPos()
        if event.reason() == QContextMenuEvent.Reason.Keyboard:
            position = self.viewport().mapToGlobal(self.visualItemRect(item).center())
        self.context_menu.popup(position)


class MainWindow(QMainWindow):
    def __init__(self, controller: AppController):
        super().__init__()
        self.controller = controller
        self.setWindowTitle(f"DrLua v{controller.version}")
        self.resize(1000, 880)
        self.tabs = QTabWidget(objectName="mainTabs")
        self.tabs.setMovable(True)
        self.setCentralWidget(self.tabs)
        self.generate_page = QWidget(objectName="generatePage")
        self.files_page = QWidget(objectName="filesPage")
        self.settings_page = QWidget(objectName="settingsPage")
        self.tabs.addTab(self.generate_page, "&Generate")
        self.tabs.addTab(self.files_page, "&Files")
        self.tabs.addTab(self.settings_page, "&Settings")
        self.build_generation()
        self.build_files()
        self.build_settings()
        self.build_menus()
        self.build_dialogs()
        controller.busyChanged.connect(self.refresh_actions)
        controller.canGenerateChanged.connect(self.refresh_actions)
        controller.generatedCommandChanged.connect(self.refresh_actions)
        controller.statusChanged.connect(self.refresh_status)
        controller.progressChanged.connect(self.refresh_progress)
        controller.outputAppended.connect(self.append_output)
        controller.updateAvailable.connect(self.offer_update)
        controller.installReady.connect(self.close)
        controller.filesListed.connect(self.show_files)
        controller.filesDeleted.connect(self.files_deleted)
        controller.fileRenamed.connect(self.file_renamed)
        controller.saveDirectoryChanged.connect(self.refresh_files)
        controller.busyChanged.connect(self.refresh_files)
        self.tabs.currentChanged.connect(self.refresh_files)
        self.refresh_actions()
        self.refresh_status()
        self.refresh_progress()
        self.sources.setFocus()

    def build_generation(self):
        form = self.controller.form
        layout = QVBoxLayout(self.generate_page)
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        fields = QWidget()
        fields_layout = QFormLayout(fields)
        fields_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        fields_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.sources = SourceEditor(objectName="sourcesField")
        self.sources.setFixedHeight(self.sources.sizeHint().height() // 2)
        self.sources.setAccessibleName("Source paths")
        self.sources.setPlaceholderText("One path per line, or separate paths with |.")
        self.sources.setTabChangesFocus(True)
        self.sources.installEventFilter(self)
        self.sources.textChanged.connect(lambda: setattr(form, "sources", self.sources.toPlainText()))
        form.sourcesChanged.connect(self.refresh_sources)
        fields_layout.addRow("&Source paths:", self.sources)
        source_buttons = QHBoxLayout()
        add_folder = QPushButton("Add &folder…", objectName="addFolderButton")
        add_folder.clicked.connect(self.add_folder)
        add_files = QPushButton("Add f&iles…", objectName="addFilesButton")
        add_files.clicked.connect(self.add_files)
        source_buttons.addWidget(add_folder)
        source_buttons.addWidget(add_files)
        source_buttons.addStretch()
        fields_layout.addRow("", source_buttons)
        self.recursive = QCheckBox("Include media in subdirectories", objectName="recursiveCheckBox")
        self.recursive.setChecked(form.recursive)
        self.recursive.toggled.connect(lambda checked: setattr(form, "recursive", checked))
        form.recursiveChanged.connect(lambda: self.recursive.setChecked(form.recursive))
        fields_layout.addRow(self.recursive)
        self.name = QLineEdit(objectName="nameField")
        self.name.setText(form.name)
        self.name.textEdited.connect(lambda text: setattr(form, "name", text))
        form.nameChanged.connect(lambda: self.name.setText(form.name))
        fields_layout.addRow("&Name:", self.name)
        self.section = QComboBox(objectName="sectionField")
        self.section.setEditable(True)
        self.section.addItems(form.sections)
        self.section.setEditText(form.section)
        self.section.editTextChanged.connect(lambda text: setattr(form, "section", text))
        form.sectionChanged.connect(lambda: self.section.setEditText(form.section))
        fields_layout.addRow("S&ection:", self.section)
        self.category = QComboBox(objectName="categoryField")
        self.category.setEditable(True)
        self.refresh_categories()
        self.category.editTextChanged.connect(lambda text: setattr(form, "category", text))
        form.categoriesChanged.connect(self.refresh_categories)
        form.categoryChanged.connect(lambda: self.category.setEditText(form.category))
        fields_layout.addRow("&Category:", self.category)
        self.group = QLineEdit(objectName="groupField")
        self.group.textEdited.connect(lambda text: setattr(form, "group", text))
        form.groupChanged.connect(lambda: self.group.setText(form.group))
        fields_layout.addRow("G&roup:", self.group)
        self.tags = QPlainTextEdit(objectName="tagsField")
        self.tags.setTabChangesFocus(True)
        self.tags.setAccessibleName("Tags")
        self.tags.setPlaceholderText("One tag per line, or comma-separated")
        self.tags.textChanged.connect(lambda: setattr(form, "tags", self.tags.toPlainText()))
        form.tagsChanged.connect(self.refresh_tags)
        fields_layout.addRow("Ta&gs:", self.tags)
        scroll.setWidget(fields)
        splitter.addWidget(scroll)
        output_panel = QWidget()
        output_layout = QVBoxLayout(output_panel)
        output_actions = QHBoxLayout()
        output_actions.addWidget(QLabel("Output"))
        output_actions.addStretch()
        copy = QPushButton("&Copy output", objectName="copyOutputButton")
        copy.clicked.connect(self.controller.copyOutput)
        output_actions.addWidget(copy)
        output_layout.addLayout(output_actions)
        self.output = QPlainTextEdit(objectName="outputText")
        self.output.setAccessibleName("Generation output")
        self.output.setReadOnly(True)
        self.output.setTabChangesFocus(True)
        self.output.setPlaceholderText("Generate a script, then copy its dofile command into the DaVinci Resolve Lua console.")
        output_layout.addWidget(self.output)
        splitter.addWidget(output_panel)
        splitter.setSizes([500, 220])
        actions = QHBoxLayout()
        self.generate_button = QPushButton("&Generate", objectName="generateButton")
        self.generate_button.clicked.connect(self.controller.generate)
        actions.addWidget(self.generate_button)
        self.cancel_button = QPushButton("Cancel", objectName="cancelButton")
        self.cancel_button.clicked.connect(self.controller.cancelGeneration)
        actions.addWidget(self.cancel_button)
        self.copy_lua = QPushButton("&Copy", objectName="copyLuaCommandButton")
        self.copy_lua.clicked.connect(self.controller.copyGeneratedCommand)
        actions.addWidget(self.copy_lua)
        self.progress = QProgressBar(objectName="generationProgress")
        self.progress.setAccessibleName("Generation progress")
        actions.addWidget(self.progress, 1)
        open_output = QPushButton("&Open output folder", objectName="openOutputButton")
        open_output.clicked.connect(self.controller.openOutput)
        actions.addWidget(open_output)
        layout.addLayout(actions)
        self.status = QLabel(objectName="statusLabel")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

    def build_files(self):
        layout = QVBoxLayout(self.files_page)
        self.file_controls = QWidget()
        directory_layout = QFormLayout(self.file_controls)
        directory_layout.setContentsMargins(0, 0, 0, 0)
        directory_layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        directory_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.save_directory = QLineEdit(self.controller.saveDirectory, objectName="saveDirectoryField")
        self.save_directory.setAccessibleName("Save directory")
        self.save_directory.editingFinished.connect(self.save_preferences)
        self.controller.saveDirectoryChanged.connect(
            lambda: self.save_directory.setText(self.controller.saveDirectory)
        )
        row = QHBoxLayout()
        row.addWidget(self.save_directory)
        browse = QPushButton("&Browse…", objectName="browseSaveDirectoryButton")
        browse.clicked.connect(self.browse_save_directory)
        row.addWidget(browse)
        open_saves = QPushButton("&Open saves folder", objectName="openSavesFolderButton")
        open_saves.clicked.connect(self.controller.openOutput)
        row.addWidget(open_saves)
        refresh = QPushButton("&Refresh", objectName="refreshFilesButton")
        refresh.clicked.connect(self.refresh_files)
        row.addWidget(refresh)
        label = QLabel("&Save directory:")
        label.setBuddy(self.save_directory)
        directory_layout.addRow(label, row)
        layout.addWidget(self.file_controls)
        self.file_search = QLineEdit(objectName="searchFilesField")
        self.file_search.setPlaceholderText("Search Files")
        self.file_search.setAccessibleName("Search Files")
        self.file_search.setClearButtonEnabled(True)
        self.file_search.textChanged.connect(self.filter_files)
        layout.addWidget(self.file_search)
        self.files = SavedFilesList(objectName="savedFilesList")
        self.files.setAccessibleName("Saved Lua files")
        self.files.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.copy_file_action = QAction("&Copy command", self.files)
        self.copy_file_action.setShortcut(QKeySequence.StandardKey.Copy)
        self.copy_file_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        self.copy_file_action.triggered.connect(self.copy_file_commands)
        self.delete_file_action = QAction("&Delete file…", self.files)
        self.delete_file_action.setShortcut(QKeySequence.StandardKey.Delete)
        self.delete_file_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        self.delete_file_action.triggered.connect(self.delete_file_commands)
        self.rename_file_action = QAction("&Rename file…", self.files)
        self.rename_file_action.setShortcut(QKeySequence(Qt.Key.Key_F2))
        self.rename_file_action.setShortcutContext(Qt.ShortcutContext.WidgetShortcut)
        self.rename_file_action.triggered.connect(self.rename_file)
        self.files.addActions([self.copy_file_action, self.rename_file_action, self.delete_file_action])
        self.files.context_menu = QMenu(self.files)
        self.files.context_menu.addAction(self.copy_file_action)
        self.files.context_menu.addAction(self.rename_file_action)
        self.files.context_menu.addSeparator()
        self.files.context_menu.addAction(self.delete_file_action)
        self.files.itemSelectionChanged.connect(self.refresh_file_actions)
        self.refresh_file_actions()
        layout.addWidget(self.files)
        self.copy_commands = QPushButton("&Copy selected commands", objectName="copySelectedCommandsButton")
        self.copy_commands.setEnabled(False)
        self.files.itemSelectionChanged.connect(
            lambda: self.copy_commands.setEnabled(bool(self.files.selectedItems()))
        )
        self.copy_commands.clicked.connect(self.copy_file_commands)
        layout.addWidget(self.copy_commands, alignment=Qt.AlignmentFlag.AlignLeft)
        self.files_status = QLabel(objectName="filesStatusLabel")
        self.files_status.setWordWrap(True)
        layout.addWidget(self.files_status)

    def refresh_file_actions(self):
        selected = self.files.selectedItems()
        self.copy_file_action.setEnabled(bool(selected))
        self.delete_file_action.setEnabled(bool(selected))
        self.rename_file_action.setEnabled(len(selected) == 1)
        self.copy_file_action.setText("&Copy command" if len(selected) == 1 else "&Copy commands")
        self.delete_file_action.setText("&Delete file…" if len(selected) == 1 else "&Delete files…")

    def rename_file(self):
        path = Path(self.files.selectedItems()[0].data(Qt.ItemDataRole.UserRole))
        self.rename_dialog = QDialog(self, objectName="renameFileDialog")
        self.rename_dialog.setWindowTitle("Rename file")
        layout = QFormLayout(self.rename_dialog)
        filename = QLineEdit(path.name, objectName="renameFilenameField")
        layout.addRow("&Filename:", filename)
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.rename_dialog.accept)
        buttons.rejected.connect(self.rename_dialog.reject)
        self.rename_dialog.accepted.connect(lambda: self.controller.renameFile(path, filename.text()))
        layout.addRow(buttons)
        self.rename_dialog.open()
        filename.setFocus()
        filename.setSelection(0, len(path.stem))

    def file_renamed(self, path):
        self.refresh_files()
        self.files_status.setText(f"Renamed file to {path.name}.")

    def delete_file_commands(self):
        paths = [Path(item.data(Qt.ItemDataRole.UserRole)) for item in self.files.selectedItems()]
        self.delete_prompt = QMessageBox(self)
        self.delete_prompt.setWindowTitle("Delete saved Lua files")
        self.delete_prompt.setIcon(QMessageBox.Icon.Warning)
        self.delete_prompt.setText("Permanently delete these saved Lua files?\n\n" + "\n".join(path.name for path in paths))
        self.delete_prompt.setInformativeText("This cannot be undone. Source media will not be deleted.")
        delete = self.delete_prompt.addButton("Delete", QMessageBox.ButtonRole.DestructiveRole)
        cancel = self.delete_prompt.addButton(QMessageBox.StandardButton.Cancel)
        self.delete_prompt.setDefaultButton(cancel)
        self.delete_prompt.setEscapeButton(cancel)
        self.delete_prompt.buttonClicked.connect(
            lambda button: self.controller.deleteFiles(paths) if button is delete else None
        )
        self.delete_prompt.open()

    def files_deleted(self, paths):
        self.refresh_files()
        self.files_status.setText(f"Deleted {len(paths)} saved Lua file(s).")

    def refresh_files(self):
        if self.tabs.currentWidget() is self.files_page and not self.controller.busy:
            self.files_status.clear()
            self.files.clear()
            self.controller.listFiles()

    def show_files(self, directory, paths):
        if directory == self.controller.profile.save_directory:
            self.files.clear()
            for path in paths:
                item = QListWidgetItem(path.name)
                item.setData(Qt.ItemDataRole.UserRole, path.as_posix())
                self.files.addItem(item)
            self.filter_files()

    def filter_files(self):
        search = self.file_search.text().casefold()
        for index in range(self.files.count()):
            item = self.files.item(index)
            hidden = search not in item.text().casefold()
            if hidden:
                item.setSelected(False)
            item.setHidden(hidden)

    def copy_file_commands(self):
        commands = []
        for index in range(self.files.count()):
            item = self.files.item(index)
            if item.isSelected():
                path = item.data(Qt.ItemDataRole.UserRole)
                equals = ""
                while f"]{equals}]" in path:
                    equals += "="
                commands.append(f"dofile([{equals}[{path}]{equals}])")
        text = "\n".join(commands)
        clipboard = QApplication.clipboard()
        clipboard.setText(text)
        count = len(commands)
        noun = "command" if count == 1 else "commands"
        if clipboard.text() == text:
            self.files_status.setText(f"Copied {count} {noun} to clipboard.")
        else:
            self.files_status.setText(f"Failed to copy {count} {noun} to clipboard.")

    def build_settings(self):
        layout = QFormLayout(self.settings_page)
        layout.setRowWrapPolicy(QFormLayout.RowWrapPolicy.WrapLongRows)
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)
        self.check_updates = QPushButton("Check for &updates", objectName="checkUpdatesButton")
        self.check_updates.clicked.connect(self.controller.checkUpdates)
        update_row = QHBoxLayout()
        update_row.addWidget(self.check_updates)
        update_row.addStretch()
        layout.addRow("Updates:", update_row)
        if self.controller.profile.no_profile:
            notice = QLabel("No profile: saved preferences are ignored. Changes apply only to this session; output defaults to temporary storage.")
            notice.setWordWrap(True)
            layout.addRow(notice)

    def build_menus(self):
        file_menu = self.menuBar().addMenu("&File")
        file_menu.setObjectName("fileMenu")
        file_menu.addAction("Add &Folder…", self.add_folder)
        file_menu.addAction("Add &Files…", self.add_files)
        file_menu.addSeparator()
        quit_action = file_menu.addAction("&Quit", self.close)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        help_menu = self.menuBar().addMenu("&Help")
        help_menu.setObjectName("helpMenu")
        help_menu.addAction("&About", self.show_about)

    def build_dialogs(self):
        self.folder_dialog = QFileDialog(self, "Add source folder")
        self.folder_dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.folder_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        self.folder_dialog.filesSelected.connect(self.append_sources)
        self.files_dialog = QFileDialog(self, "Add source files")
        self.files_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        self.files_dialog.filesSelected.connect(self.append_sources)
        self.save_dialog = QFileDialog(self, "Select save directory")
        self.save_dialog.setFileMode(QFileDialog.FileMode.Directory)
        self.save_dialog.setOption(QFileDialog.Option.ShowDirsOnly)
        self.save_dialog.fileSelected.connect(self.select_save_directory)

    def eventFilter(self, watched, event):
        if watched is self.sources and event.type() == QEvent.Type.FocusOut:
            self.controller.form.inferSource()
        return super().eventFilter(watched, event)

    def refresh_sources(self):
        if self.sources.toPlainText() != self.controller.form.sources:
            self.sources.setPlainText(self.controller.form.sources)

    def refresh_tags(self):
        if self.tags.toPlainText() != self.controller.form.tags:
            self.tags.setPlainText(self.controller.form.tags)

    def refresh_categories(self):
        with QSignalBlocker(self.category):
            self.category.clear()
            self.category.addItems(self.controller.form.categories)
            self.category.setCurrentIndex(-1)
            self.category.setEditText(self.controller.form.category)

    def refresh_actions(self):
        self.generate_button.setEnabled(self.controller.canGenerate)
        self.cancel_button.setEnabled(self.controller.canCancel)
        self.copy_lua.setEnabled(bool(self.controller.generatedCommand) and not self.controller.busy)
        self.check_updates.setEnabled(not self.controller.busy)
        self.settings_page.setEnabled(not self.controller.busy)
        self.file_controls.setEnabled(not self.controller.busy)

    def refresh_status(self):
        self.status.setText(self.controller.status)

    def refresh_progress(self):
        self.progress.setRange(0, self.controller.progressMaximum)
        self.progress.setValue(self.controller.progressValue)

    def append_output(self, message):
        self.output.moveCursor(QTextCursor.MoveOperation.End)
        self.output.insertPlainText(message)
        self.output.ensureCursorVisible()

    def add_folder(self):
        self.folder_dialog.open()

    def add_files(self):
        self.files_dialog.open()

    def append_sources(self, paths):
        self.controller.form.appendUrls([QUrl.fromLocalFile(path) for path in paths])
        self.tabs.setCurrentWidget(self.generate_page)

    def save_preferences(self):
        if self.controller.saveDirectory != self.save_directory.text():
            self.controller.saveDirectory = self.save_directory.text()

    def browse_save_directory(self):
        self.save_dialog.setDirectory(self.controller.saveDirectory)
        self.save_dialog.open()

    def select_save_directory(self, directory):
        self.controller.saveDirectory = directory

    def offer_update(self, version):
        self.update_prompt = QMessageBox(
            QMessageBox.Icon.Question, "Update DrLua",
            f"DrLua {version} is available. Download and install it?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, self,
        )
        self.update_prompt.setDefaultButton(QMessageBox.StandardButton.No)
        self.update_prompt.finished.connect(self.update_decided)
        self.update_prompt.open()

    def update_decided(self, result):
        if result == QMessageBox.StandardButton.Yes:
            self.controller.acceptUpdate()
        else:
            self.controller.declineUpdate()

    def show_about(self):
        self.about_dialog = QDialog(self, objectName="aboutDialog")
        self.about_dialog.setWindowTitle("About DrLua")
        layout = QVBoxLayout(self.about_dialog)
        layout.addWidget(QLabel(f"DrLua\nVersion {self.controller.version}"))
        link = QLabel('<a href="https://github.com/electblake/DrLua">GitHub repository</a>')
        link.setOpenExternalLinks(True)
        link.setTextInteractionFlags(Qt.TextInteractionFlag.TextBrowserInteraction)
        layout.addWidget(link)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.about_dialog.reject)
        layout.addWidget(buttons)
        self.about_dialog.open()

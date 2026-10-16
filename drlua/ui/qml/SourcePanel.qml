pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

ColumnLayout {
    id: panel
    required property FormModel form
    spacing: 6
    Label { text: qsTr("Source paths"); font.bold: true }
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        ScrollView {
            Layout.fillWidth: true
            Layout.preferredHeight: 100
            TextArea {
                id: sources
                objectName: "sourcesField"
                text: panel.form.sources
                placeholderText: qsTr("Add folders or files, or paste paths here")
                Accessible.name: qsTr("Source paths")
                selectByMouse: true
                wrapMode: TextEdit.NoWrap
                focus: true
                Component.onCompleted: sources.forceActiveFocus()
                KeyNavigation.tab: folderButton
                KeyNavigation.priority: KeyNavigation.BeforeItem
                onTextChanged: panel.form.sources = sources.text
                onActiveFocusChanged: {
                    if (!sources.activeFocus)
                        panel.form.inferSource()
                }
            }
        }
        ColumnLayout {
            Button {
                id: folderButton
                objectName: "addFolderButton"
                text: qsTr("Add folder…")
                Layout.fillWidth: true
                onClicked: folderLoader.active = true
            }
            Button {
                objectName: "addFilesButton"
                text: qsTr("Add files…")
                Layout.fillWidth: true
                onClicked: filesLoader.active = true
            }
        }
    }
    Label {
        Layout.fillWidth: true
        text: qsTr("One path per line, or separate paths with |.")
        wrapMode: Text.WordWrap
    }
    Loader {
        id: folderLoader
        active: false
        sourceComponent: SourceFolderDialog {
            form: panel.form
            onDismissed: folderLoader.active = false
        }
        onLoaded: {
            if (folderLoader.status === Loader.Ready)
                (folderLoader.item as SourceFolderDialog).open()
        }
    }
    Loader {
        id: filesLoader
        active: false
        sourceComponent: SourceFilesDialog {
            form: panel.form
            onDismissed: filesLoader.active = false
        }
        onLoaded: {
            if (filesLoader.status === Loader.Ready)
                (filesLoader.item as SourceFilesDialog).open()
        }
    }
}

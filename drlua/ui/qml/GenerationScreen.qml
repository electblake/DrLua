pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

Pane {
    id: screen
    required property AppController controller
    padding: 24

    ColumnLayout {
        anchors.fill: parent
        spacing: 16
        AppHeader {
            Layout.fillWidth: true
            controller: screen.controller
        }
        SplitView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            orientation: Qt.Vertical
            GenerationForm {
                SplitView.fillWidth: true
                SplitView.preferredHeight: 430
                SplitView.minimumHeight: 240
                form: screen.controller.form
            }
            OutputPanel {
                SplitView.fillWidth: true
                SplitView.fillHeight: true
                SplitView.minimumHeight: 130
                controller: screen.controller
            }
        }
        GenerationActions {
            Layout.fillWidth: true
            controller: screen.controller
        }
    }
    Loader {
        id: updateLoader
        property string releaseVersion: ""
        active: false
        sourceComponent: UpdatePrompt {
            controller: screen.controller
            releaseVersion: updateLoader.releaseVersion
            onClosed: updateLoader.active = false
        }
        onLoaded: {
            if (updateLoader.status === Loader.Ready)
                (updateLoader.item as UpdatePrompt).open()
        }
    }
    Connections {
        target: screen.controller
        function onUpdateAvailable(version: string): void {
            updateLoader.releaseVersion = version
            updateLoader.active = true
        }
    }
}

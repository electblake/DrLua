import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

ColumnLayout {
    id: actions
    required property AppController controller
    spacing: 10
    RowLayout {
        Layout.fillWidth: true
        spacing: 12
        Button {
            objectName: "generateButton"
            text: qsTr("Generate Lua script")
            highlighted: true
            enabled: actions.controller.canGenerate
            onClicked: actions.controller.generate()
        }
        ProgressBar {
            objectName: "generationProgress"
            Layout.fillWidth: true
            from: 0
            to: Number(actions.controller.progressMaximum)
            value: Number(actions.controller.progressValue)
            Accessible.name: qsTr("Generation progress")
        }
        Button {
            objectName: "openOutputButton"
            text: qsTr("Open output folder")
            onClicked: actions.controller.openOutput()
        }
    }
    Label {
        objectName: "statusLabel"
        Layout.fillWidth: true
        text: actions.controller.status
        wrapMode: Text.WordWrap
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

RowLayout {
    id: header
    required property AppController controller
    spacing: 16
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        Label {
            text: qsTr("DrLua")
            font.pointSize: ApplicationWindow.window.font.pointSize * 1.44
            font.bold: true
        }
        Label {
            Layout.fillWidth: true
            text: qsTr("DaVinci Resolve Lua scripts · v%1").arg(header.controller.version)
            wrapMode: Text.WordWrap
        }
    }
    Button {
        objectName: "checkUpdatesButton"
        text: qsTr("Check for updates")
        enabled: !header.controller.busy
        onClicked: header.controller.checkUpdates()
    }
}

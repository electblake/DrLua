import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

Pane {
    id: panel
    required property AppController controller
    padding: 0
    topPadding: 12
    ColumnLayout {
        anchors.fill: parent
        spacing: 8
        RowLayout {
            Layout.fillWidth: true
            Label {
                Layout.fillWidth: true
                text: qsTr("Output")
                font.bold: true
            }
            Button {
                objectName: "copyOutputButton"
                text: qsTr("Copy output")
                onClicked: panel.controller.copyOutput()
            }
        }
        ScrollView {
            Layout.fillWidth: true
            Layout.fillHeight: true
            TextArea {
                id: output
                objectName: "outputText"
                readOnly: true
                selectByMouse: true
                textFormat: TextEdit.PlainText
                wrapMode: TextEdit.Wrap
                font.family: "Consolas"
                Accessible.name: qsTr("Generation output")
                placeholderText: qsTr("Generate a script, then copy its dofile command into the DaVinci Resolve Lua console.")
                Keys.onTabPressed: event => { output.nextItemInFocusChain(true).forceActiveFocus(); event.accepted = true }
            }
        }
    }
    Connections {
        target: panel.controller
        function onOutputAppended(message: string): void {
            output.insert(output.length, message)
            output.cursorPosition = output.length
        }
    }
}

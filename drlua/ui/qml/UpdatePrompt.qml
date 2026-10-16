import QtQuick
import QtQuick.Controls.FluentWinUI3
import DrLua

Dialog {
    id: dialog
    required property AppController controller
    required property string releaseVersion
    parent: Overlay.overlay
    anchors.centerIn: parent
    width: Math.min(480, parent.width - 48)
    title: qsTr("DrLua update available")
    modal: true
    standardButtons: Dialog.Yes | Dialog.No
    closePolicy: Popup.CloseOnEscape
    contentItem: Label {
        text: qsTr("DrLua %1 is available.\n\nDownload the update and close DrLua to run setup? The current form will be discarded.").arg(dialog.releaseVersion)
        wrapMode: Text.WordWrap
    }
    onAccepted: dialog.controller.acceptUpdate()
    onRejected: dialog.controller.declineUpdate()
}

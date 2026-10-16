import QtQuick.Dialogs
import DrLua

FolderDialog {
    id: dialog
    required property FormModel form
    signal dismissed()
    title: qsTr("Add source folder")
    onAccepted: {
        dialog.form.appendUrls([dialog.selectedFolder])
        dialog.dismissed()
    }
    onRejected: dialog.dismissed()
}

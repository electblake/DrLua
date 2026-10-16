import QtQuick.Dialogs
import DrLua

FileDialog {
    id: dialog
    required property FormModel form
    signal dismissed()
    title: qsTr("Add media or export files")
    fileMode: FileDialog.OpenFiles
    onAccepted: {
        dialog.form.appendUrls(dialog.selectedFiles)
        dialog.dismissed()
    }
    onRejected: dialog.dismissed()
}

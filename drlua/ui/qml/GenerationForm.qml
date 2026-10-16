import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

ScrollView {
    id: panel
    required property FormModel form
    contentWidth: availableWidth
    clip: true

    function revealFocus(): void {
        const focused = panel.Window.window.activeFocusItem
        if (!focused)
            return
        let ancestor = focused
        while (ancestor && ancestor !== panel)
            ancestor = ancestor.parent
        if (ancestor !== panel)
            return
        const flickable = panel.contentItem as Flickable
        const top = focused.mapToItem(flickable.contentItem, 0, 0).y
        if (top < flickable.contentY)
            flickable.contentY = top
        else if (top + focused.height > flickable.contentY + flickable.height)
            flickable.contentY = top + focused.height - flickable.height
    }
    Connections {
        target: panel.Window.window
        function onActiveFocusItemChanged(): void { panel.revealFocus() }
    }
    ColumnLayout {
        width: panel.availableWidth
        spacing: 16
        SourcePanel {
            Layout.fillWidth: true
            form: panel.form
        }
        MetadataPanel {
            Layout.fillWidth: true
            form: panel.form
        }
        ColumnLayout {
            Layout.fillWidth: true
            spacing: 4
            Label { text: qsTr("Tags") }
            ScrollView {
                Layout.fillWidth: true
                Layout.preferredHeight: 90
                TextArea {
                    id: tags
                    objectName: "tagsField"
                    text: panel.form.tags
                    placeholderText: qsTr("One tag per line, or comma-separated")
                    Accessible.name: qsTr("Tags")
                    wrapMode: TextEdit.Wrap
                    selectByMouse: true
                    Keys.onTabPressed: event => { tags.nextItemInFocusChain(true).forceActiveFocus(); event.accepted = true }
                    onTextChanged: panel.form.tags = tags.text
                }
            }
        }
    }
}

import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import DrLua

GridLayout {
    id: panel
    required property FormModel form
    columns: panel.width < 760 ? 2 : 3
    columnSpacing: 12
    rowSpacing: 10
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        Label { text: qsTr("Name") }
        TextField {
            id: nameField
            objectName: "nameField"
            Layout.fillWidth: true
            text: panel.form.name
            Accessible.name: qsTr("Name")
            onTextEdited: panel.form.name = nameField.text
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        Label { text: qsTr("Section") }
        ComboBox {
            id: section
            objectName: "sectionField"
            Layout.fillWidth: true
            editable: true
            model: panel.form.sections
            editText: panel.form.section
            Accessible.name: qsTr("Section")
            onEditTextChanged: panel.form.section = section.editText
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        spacing: 4
        Label { text: qsTr("Category") }
        ComboBox {
            id: category
            objectName: "categoryField"
            Layout.fillWidth: true
            editable: true
            model: panel.form.categories
            currentIndex: -1
            editText: panel.form.category
            Accessible.name: qsTr("Category")
            onEditTextChanged: panel.form.category = category.editText
        }
    }
    ColumnLayout {
        Layout.fillWidth: true
        Layout.columnSpan: panel.columns === 3 ? 3 : 1
        spacing: 4
        Label { text: qsTr("Group") }
        TextField {
            id: group
            objectName: "groupField"
            Layout.fillWidth: true
            text: panel.form.group
            Accessible.name: qsTr("Group")
            onTextEdited: panel.form.group = group.text
        }
    }
}

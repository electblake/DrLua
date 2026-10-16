import QtQuick
import QtQuick.Controls
import DrLua

ApplicationWindow {
    id: window
    required property AppController controller
    width: 1000
    height: 880
    minimumWidth: 700
    minimumHeight: 660
    visible: true
    title: qsTr("DrLua v%1").arg(window.controller.version)
    LayoutMirroring.enabled: Qt.locale().textDirection === Qt.RightToLeft
    LayoutMirroring.childrenInherit: true

    GenerationScreen {
        anchors.fill: parent
        controller: window.controller
    }
}

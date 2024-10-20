
import QtQuick 
import QtQuick.Layouts
import QtQuick.Controls 
import QtQuick.Window 
import QtQuick.Controls.Material 

ApplicationWindow {
    id: root
    title: qsTr("PaperMoon")
    width: 1280
    height: 720
    visible: true

    property color baseWinBg: Qt.rgba(255,255,255,0.5)
    property int   baseFontSize: 20

    Component.onCompleted: {
        console.log("Window loaded")
        //console.log(baseWinBg)  // 检查是否能够访问常量
    }

    menuBar: MenuBar{
        
    }
    footer: ToolBar{

    }
    Image {
        anchors.centerIn: parent
        property var defaultBgImg :"../imp.png"
        property var userBgImg :""
        source: userBgImg? userBgImg : defaultBgImg
        fillMode: Image.PreserveAspectCrop
        clip: true
    }

    Rectangle{id: leftFrame
        width: parent.width *2 /5 - 10
        height: 640
        color: baseWinBg 
        anchors.verticalCenter: parent.verticalCenter 
        anchors.left: parent.left 
        anchors.leftMargin: 50 
        clip: true
        
        property var tableHeaderArray: ['quest',
                                            "friend class",
                                            'friend',  
                                            'stage count',
                                            'ap',                              
                                            'quest threshold',
                                            'friend threshold',
                                            'port' ]
        Grid{
            id: userTable
            rows: 8
            columns: 2
            anchors.centerIn: parent 
            anchors.fill: parent 
            leftPadding: 30
            rightPadding: 30
            topPadding: 30
            bottomPadding: 90
            columnSpacing: 50
            rowSpacing: 30
            width: parent.width*2 /3 -10
            flow: Grid.TopToBottom
            
            Repeater{
                id: tableHeader
                model:  8
                property int index : 0
                Label{
                    text: leftFrame.tableHeaderArray[index]
                    font.pixelSize: baseFontSize
                    horizontalAlignment: Text.AlignRight
                    clip: true
                }
            }
            Repeater{
                id: tableEntry
                model: 8
                Rectangle{
                    width:200; height: 30
                    border.width: 2
                    color: 'whitesmoke'
                    radius: 5 
                    TextInput{
                        anchors.fill: parent 
                        anchors.margins: 5
                        text: "Text Input 1"
                        color:'gray' 
                        clip: true
                    }
                }
            }
        }
        Button{
            text: "BBB set"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 30
            width: parent.width -40
        }
    }
    Rectangle{id: rightFrame
        width: parent.width *2 /5 - 10
        height: 640
        anchors.verticalCenter: parent.verticalCenter 
        anchors.left: leftFrame.right
        anchors.leftMargin: 30 
        anchors.right: rightBar 
        anchors.rightMargin: 30 
        color: baseWinBg

        Button{
            text: "BBB Go"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 30
            width: parent.width -40

            onClicked: {
                BBB.go()
            }
        }
    }
    Rectangle{id: rightBar
        width: 100
        height: 640
        anchors.verticalCenter: parent.verticalCenter 
        anchors.right: parent.right 
        color: 'white'
    }
    
}




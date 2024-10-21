
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
        height: 20
    }
    footer: ToolBar{
        height: 20
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
        width: parent.width *2 /5 + 40
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
        Grid{id: userTable
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
            width: parent.width*2 /3 -30
            flow: Grid.TopToBottom
            
            Repeater{id: tableHeader
                model:  8
                property int index : 0
                Label{
                    width: 200
                    text: leftFrame.tableHeaderArray[index]
                    font.pixelSize: baseFontSize
                    horizontalAlignment: Text.AlignRight
                    clip: true
                }
            }
            Repeater{ id: tableEntry
                model: 6
                TextField{
                    height: 35
                    topInset: 5
                    placeholderText: "Text Input 1"
                    placeholderTextColor:'gray' 
                    clip: true

                    background: Rectangle{
                        anchors.fill: parent
                        border.width: 0
                        color: 'whitesmoke'
                        radius: 5
                    }
                    
                }
            }
            MyTextField{
                id: friendThreasholdEntry
                validator: DoubleValidator {
                    notation: DoubleValidator.StandardNotation	
                    bottom: 0.00
                    top: 0.99
                    decimals: 2
                }
            }
            TextField{
                id: portEntry
                height: 35
                topInset: 5
                placeholderText: "Your IP Port"
                placeholderTextColor:'gray' 
                clip: true

                background: Rectangle{
                    anchors.fill: parent
                    border.width: 0
                    color: 'whitesmoke'
                    radius: 5
                }
                //inputMask: '000.000.000.000;_'
                validator: DoubleValidator {
                        bottom: 0.00
                        top: 0.99
                        decimals: 2
                    }
            }
        }
        Button{
            text: "BBB Set"
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 30
            width: parent.width -40
            onClicked: {
                BBB.setup()
            }
        }
    }
    Rectangle{id: rightFrame
        width: parent.width *2 /5 - 10
        height: 640
        anchors.verticalCenter: parent.verticalCenter 
        anchors.left: leftFrame.right
        anchors.leftMargin: 30 
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




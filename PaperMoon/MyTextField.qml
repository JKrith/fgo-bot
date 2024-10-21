import QtQuick 

import QtQuick.Controls 
import QtQuick.Controls.Material 


TextField {
    //property Component myComponent: myTF
    //property alias text : myTF.placeholderText
    //property alias inputMask : myTF.inputMask
    //property alias validator : myTF.validator
        
    placeholderText: "Text Input"
    placeholderTextColor:'gray' 
    clip: true
    background: Rectangle{
        implicitWidth: 200
        implicitHeight: 40
        color: 'whitesmoke'
        radius: 5
    }

}
    

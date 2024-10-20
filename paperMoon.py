from PyQt6.QtCore import QCoreApplication, QDir, QFile, QStandardPaths, QObject, pyqtSlot
from PyQt6.QtGui import QGuiApplication, QColor
from PyQt6.QtQml import QQmlApplicationEngine
from PyQt6.QtSql import QSqlDatabase

import logging
import sys
import threading
import subprocess

from fgobot import bot

class BBB(QObject):

    def __init__(self, parent=...):
        super().__init__()

        self.masterCommand={}

    @pyqtSlot()
    def setup(self):
        #
        if bool('args is enough'):
            self.boringBattleBot = bot.BattleBot(
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand[''],
                self.masterCommand['']
            )
        else:
            pass
    @pyqtSlot()
    def go(self):
        try:
            self.boringBattleBot.run(max_loops=3 )
        except AttributeError:
            print('Sorry!')
        else:    
            print("bb~~go!")

if __name__ == "__main__":
    bbb = BBB()
    app = QGuiApplication(sys.argv)
    QCoreApplication.setOrganizationName("QtProject")
    QCoreApplication.setApplicationName("Chat Tutorial")

    engine = QQmlApplicationEngine()
    engine.addImportPath(sys.path[0])
    engine.rootContext().setContextProperty('BBB', bbb)
    engine.load("./PaperMoon/PaperMoon.qml")

    if not engine.rootObjects():
        sys.exit(-1)

    app.exec()
    del engine
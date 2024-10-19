from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtGui import QGuiApplication
import sys
import threading
import subprocess


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()
    engine.addImportPath(sys.path[0])
    engine.loadFromModule('PaperMoon', 'PaperMoon')
    # sys.path
    # engine.load('C:\\Users\\86189\\Documents\\fgo-bot-master\\Main.qml')
    if not engine.rootObjects():
        sys.exit(-1)
    exit_code = app.exec()
    del engine
    sys.exit(exit_code)
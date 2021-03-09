from features import Assistant
from feature_files.natural_language import talk
import inspect
from feature_files.speak_and_get_audio import speak, get_audio
from PyQt5 import QtGui
from PyQt5 import QtCore
from PyQt5.QtCore import *

TEXT = ''

import PyQt5.uic
from PyQt5.QtWidgets import *
import sys

bot = Assistant("Cake")

class MainBackgroundThread(QThread):
    def __init__(self, text):
        QThread.__init__(self)
        self.text = text
    def run(self):
        speak(self.text)


class VoiceWorker(QObject):
    finished = pyqtSignal()
    progress = pyqtSignal(str)
    def run(self):
        global TEXT
        TEXT = ''
        x = get_audio()
        TEXT = x
        self.progress.emit(TEXT)
        self.finished.emit()

class UiMainWindow(QMainWindow):
    def __init__(self):
        super(UiMainWindow, self).__init__()
        PyQt5.uic.loadUi('UI/main.ui', self)
        self.btn_toggle.clicked.connect(lambda: self.slideLeftMenu())
        self.actionExit.triggered.connect(lambda: sys.exit())
        self.actionLog_out.triggered.connect(lambda: self.showLoginWindow())
        self.submit.clicked.connect(self.onsend)
        self.voiceinput.clicked.connect(self.onvoice)
        self.parameter_entered = False
        self.parameter = None
        self.current_function = None
        self.audio = VoiceWorker()

    def slideLeftMenu(self):
        width = self.frame_2.width()
        if width < 101:
            newWidth = 101
        else:
            newWidth = 0
        self.animation = QPropertyAnimation(self.frame_2, b"geometry")
        self.animation.setDuration(250)
        self.animation.setStartValue(QRect(0, 40, width, 801))
        self.animation.setEndValue(QRect(0, 40, newWidth, 801))
        self.animation.setEasingCurve(QtCore.QEasingCurve.InOutQuart)
        self.animation.start()

    # noinspection PyUnresolvedReferences
    def onvoice(self):
        global TEXT
        self.thread = QThread()
        self.voiceworker = VoiceWorker()
        self.voiceworker.moveToThread(self.thread)
        self.thread.started.connect(self.voiceworker.run)
        self.voiceworker.finished.connect(self.talkOnVoice)
        self.voiceworker.finished.connect(self.thread.quit)
        self.voiceworker.finished.connect(self.voiceworker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def talkOnVoice(self):
        text = TEXT
        self.textinput.setText(text)
        if self.parameter_entered:
            self.parameter = str(text)
        if not self.parameter is None and not self.current_function is None:
            res = self.current_function(self.parameter, reqs_confirm=False)
            self.chatrec.append(res)
            QtGui.QGuiApplication.processEvents()
            self.worker = MainBackgroundThread(res)
            self.worker.start()
            self.parameter_entered = False
            self.current_function = None
            self.parameter = None
            self.textinput.setText(TEXT)
            return
        x = self.return_response(text)
        if isinstance(x, dict):
            res = x.get("error")
            self.chatrec.append(res)
            self.parameter_entered = True
            QtGui.QGuiApplication.processEvents()
            self.worker = MainBackgroundThread(res)
            self.worker.start()
            self.textinput.setText(TEXT)
            return
        self.chatrec.append(x)
        QtGui.QGuiApplication.processEvents()
        self.worker = MainBackgroundThread(x)
        self.worker.start()
        return

    def onsend(self):
        text = self.textinput.toPlainText().lower()
        if self.parameter_entered:
            self.parameter = str(text)
        if not self.parameter is None and not self.current_function is None:
            res = self.current_function(self.parameter, reqs_confirm=False)
            self.chatrec.append(res)
            QtGui.QGuiApplication.processEvents()
            self.worker = MainBackgroundThread(res)
            self.worker.start()
            self.parameter_entered = False
            self.current_function = None
            self.parameter = None
            self.textinput.setText("")
            return
        x = self.return_response(text)
        if isinstance(x, dict):
            res = x.get("error")
            self.chatrec.append(res)
            self.parameter_entered = True
            QtGui.QGuiApplication.processEvents()
            self.worker = MainBackgroundThread(res)
            self.worker.start()
            self.textinput.setText("")
            return
        self.chatrec.append(x)
        QtGui.QGuiApplication.processEvents()
        self.worker = MainBackgroundThread(x)
        self.worker.start()
        self.textinput.setText("")
        return

    def return_response(self, text=''):
        x = talk(text)
        if x[1] == "function":
            a = inspect.getmembers(Assistant)
            y = getattr(bot, x[0])
            result = y()
            if isinstance(result, dict):
                if self.parameter_entered:
                    return y(self.parameter, reqs_confirm=False)
                else:
                    self.current_function = y
                    return result
            else:
                return result
        else:
            return x[0]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = UiMainWindow()
    widget.show()
    sys.exit(app.exec_())



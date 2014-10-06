import os
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import rtmidi

class Binding(QWidget):

    changed = pyqtSignal()
    removeMe = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.type = 0
        self.noteNum = 0
        self.ccNum = 0
        self.ccValue = 0
        self.cmd = ''

        self.removeButton = QPushButton("-", self)
        self.removeButton.setMaximumSize(50, 50)
        self.removeButton.clicked.connect(self._removeMe)

        self.typeBox = QComboBox()
        self.typeBox.addItem("Note")
        self.typeBox.addItem("CC")
        self.typeBox.currentIndexChanged.connect(self.setType)

        self.ccNumBox = QComboBox()
        for i in range(128):
            self.ccNumBox.addItem(str(i))
        self.ccNumBox.currentIndexChanged.connect(self.setCCNum)

        self.ccValueBox = QComboBox()
        for i in range(128):
            self.ccValueBox.addItem(str(i))
        self.ccValueBox.currentIndexChanged.connect(self.setCCValue)

        self.noteNumBox = QComboBox()
        for i in range(128):
            self.noteNumBox.addItem(rtmidi.MidiMessage.getMidiNoteName(i))
        self.noteNumBox.currentIndexChanged.connect(self.setNoteNum)

        self.cmdEdit = QLineEdit(self)
        self.cmdEdit.setMinimumWidth(150)
        self.cmdEdit.textChanged[str].connect(self.setCmd)

        self.findButton = QPushButton("...", self)
        self.findButton.setMaximumSize(50, 50)
        self.findButton.clicked.connect(self.findCommand)

        self.setType(0)

        Layout = QHBoxLayout()
        Layout.addWidget(self.removeButton)
        Layout.addWidget(self.typeBox)
        Layout.addWidget(self.noteNumBox)
        Layout.addWidget(self.ccNumBox)
        Layout.addWidget(self.ccValueBox)
        Layout.addWidget(self.cmdEdit)
        Layout.addWidget(self.findButton)
        self.setLayout(Layout)
    
    def readSettings(self, settings):
        self.setType(settings.value('type', type=int))
        self.setNoteNum(settings.value('noteNum', type=int))
        self.setCCNum(settings.value('ccNum', type=int))
        self.setCCValue(settings.value('ccValue', type=int))
        self.setCmd(settings.value('cmd', type=str))

    def writeSettings(self, settings):
        settings.setValue('type', self.type)
        settings.setValue('noteNum', self.noteNum)
        settings.setValue('ccNum', self.ccNum)
        settings.setValue('ccValue', self.ccValue)
        settings.setValue('cmd', self.cmd)

    def _removeMe(self):
        self.removeMe.emit(self)

    def setType(self, iType):
        self.typeBox.setCurrentIndex(iType)
        self.type = iType
        if iType == 0:
            self.noteNumBox.show()
            self.ccNumBox.hide()
            self.ccValueBox.hide()
        else:
            self.noteNumBox.hide()
            self.ccNumBox.show()
            self.ccValueBox.show()

    def setCCNum(self, x):
        self.ccNumBox.setCurrentIndex(x)
        self.ccNum = x

    def setCCValue(self, x):
        self.ccValueBox.setCurrentIndex(x)
        self.ccValue = x

    def setNoteNum(self, x):
        self.noteNumBox.setCurrentIndex(x)
        self.noteNum = x

    def setCmd(self, text):
        self.cmdEdit.setText(text)
        self.cmd = text
        self.changed.emit()

    def findCommand(self):
        ret = QFileDialog.getOpenFileName(self, "Open Program",
                                          "",
                                          "All Files (*.*)")
        if ret[0]:
            self.setCmd(ret[0])

    def match(self, m):
        if self.type == 0:
            ok = m.getNoteNumber() == self.noteNumBox.currentIndex()
        elif self.type == 1:
            ok =  \
                m.getControllerNumber() == self.ccNumBox.currentIndex() and \
                m.getControllerValue() == self.ccValueBox.currentIndex()
        if ok:
            cmd = self.cmdEdit.text()
            if os.name == 'posix':
                cmd = 'open ' + cmd
            else:
                cmd = 'start ' + cmd
            os.system(cmd)



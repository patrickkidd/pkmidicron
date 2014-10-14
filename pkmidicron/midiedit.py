from pyqt_shim import *
from rtmidi import MidiMessage
from .util import *


class MidiEdit(QWidget):

    changed = pyqtSignal(MidiMessage)

    def __init__(self, parent=None, any=False):
        QWidget.__init__(self, parent)

        self.midi = MidiMessage()

        self.typeBox = QComboBox(self)
        self.typeBox.addItem("Note")
        self.typeBox.addItem("CC")
        self.typeBox.currentIndexChanged.connect(self.setType)

        self.ccNumBox = QComboBox(self)
        for i in range(128):
            name = MidiMessage.getControllerName(i)
            if name:
                name = ': (%s)' % name
            self.ccNumBox.addItem('%i %s' % (i, name))
        if any:
            self.ccNumBox.addItem(ANY_TEXT)
        self.ccNumBox.currentIndexChanged.connect(self.setCCNum)

        self.ccValueBox = QComboBox(self)
        for i in range(128):
            self.ccValueBox.addItem(str(i))
        if any:
            self.ccValueBox.addItem(ANY_TEXT)
        self.ccValueBox.currentIndexChanged.connect(self.setCCValue)

        self.noteNumBox = QComboBox(self)
        for i in range(128):
            self.noteNumBox.addItem('%i (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        if any:
            self.noteNumBox.addItem(ANY_TEXT)
        self.noteNumBox.currentIndexChanged.connect(self.setNoteNum)

        self.noteVelBox = QComboBox(self)
        for i in range(128):
            self.noteVelBox.addItem(str(i))
        if any:
            self.noteVelBox.addItem(ANY_TEXT)
        self.noteVelBox.currentIndexChanged.connect(self.setNoteVel)

        Layout = QHBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.typeBox)
        Layout.addWidget(self.ccNumBox)
        Layout.addWidget(self.ccValueBox)
        Layout.addWidget(self.noteNumBox)
        Layout.addWidget(self.noteVelBox)
        self.setLayout(Layout)

        # init

        self.typeMap = {
            0: [ # note
                self.noteNumBox,
                self.noteVelBox
            ],
            1: { # cc
                self.ccNumBox,
                self.ccValueBox
            }
        }

        self.setType(0)
        self.changed.connect(self._onChanged)
        self._onChanged()

    def readSettings(self, settings):
        self.setType(settings.value('type', type=int))
        self.setNoteNum(settings.value('noteNum', type=int))
        self.setNoteVel(settings.value('noteVel', type=int))
        self.setCCNum(settings.value('ccNum', type=int))
        self.setCCValue(settings.value('ccValue', type=int))

    def writeSettings(self, settings):        
        settings.setValue('type', self.typeBox.currentIndex())
        settings.setValue('noteNum', self.noteNumBox.currentIndex())
        settings.setValue('noteVel', self.noteVelBox.currentIndex())
        settings.setValue('ccNum', self.ccNumBox.currentIndex())
        settings.setValue('ccValue', self.ccValueBox.currentIndex())

    def _onChanged(self):
        if self.typeBox.currentIndex() == 0:
            self.midi = MidiMessage.noteOn(1,
                                           self.noteNumBox.currentIndex(),
                                           self.noteVelBox.currentIndex())
        elif self.typeBox.currentIndex() == 1:
            self.midi = MidiMessage.controllerEvent(1,
                                                    self.ccNumBox.currentIndex(),
                                                    self.ccValueBox.currentIndex())
        

    def setType(self, iType):
        self.typeBox.setCurrentIndex(iType)
        for k, v in self.typeMap.items():
            for v2 in v:
                v2.hide()
        for w in self.typeMap[iType]:
            w.show()
        self.changed.emit(self.midi)

    def setCCNum(self, x):
        if x != self.ccNumBox.currentIndex():
            self.ccNumBox.setCurrentIndex(x)
        self.changed.emit(self.midi)

    def setCCValue(self, x):
        if x != self.ccValueBox.currentIndex():
            self.ccValueBox.setCurrentIndex(x)
        self.changed.emit(self.midi)

    def setNoteNum(self, x):
        if x != self.noteNumBox.currentIndex():
            self.noteNumBox.setCurrentIndex(x)
        self.changed.emit(self.midi)

    def setNoteVel(self, x):
        if x != self.noteVelBox.currentIndex():
            self.noteVelBox.setCurrentIndex(x)
        self.changed.emit(self.midi)

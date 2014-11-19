from rtmidi import MidiMessage, RtMidiIn
from .pyqt_shim import *
from . import util, patch
from .ports import inputs, outputs

class MidiEdit(QWidget):

    def portName(self):
        return self.portBox.currentText()
    def setPortName(self, x):
        self.portBox.setCurrentText(x)
    portName = pyqtProperty(str, portName, setPortName)

    def __init__(self, parent=None, any=False, all=False, portBox=False, input=True):
        QWidget.__init__(self, parent)

        self.block = False
        self.any = any
        self.all = all
        self.input = input

        self.midimessage = None

        self.portBox = QComboBox()
        ports = input and inputs or outputs
        for name in ports().allPorts():
            self.portBox.addItem(name)
        ports().portAdded.connect(self.addPortName)
        ports().portRemoved.connect(self.removePortName)
        if any:
            self.portBox.addItem(util.ANY_TEXT)
        if all:
            self.portBox.addItem(util.ALL_TEXT)
        self.portBox.addItem(util.NONE_TEXT)
        self.portBox.setMinimumWidth(100)
        self.portBox.currentTextChanged.connect(self.updateValue)
        if not portBox:
            self.portBox.hide()

        self.channelBox = QComboBox(self)
        for i in range(1, 17):
            self.channelBox.addItem('Channel %i' % i)
        self.channelBox.currentIndexChanged.connect(self.updateValue)
        if any:
            self.channelBox.addItem(util.ANY_TEXT)
        if all:
            self.channelBox.addItem(util.ALL_TEXT)

        self.typeBox = QComboBox(self)
        self.typeBox.addItem("Note On")
        self.typeBox.addItem("Note Off")
        self.typeBox.addItem("CC")
        self.typeBox.addItem("Aftertouch")
        self.typeBox.currentIndexChanged.connect(self.setType)

        self.ccNumBox = QComboBox(self)
        for i in range(128):
            name = MidiMessage.getControllerName(i)
            if name:
                name = ': (%s)' % name
            self.ccNumBox.addItem('%i %s' % (i, name))
        if any:
            self.ccNumBox.addItem(util.ANY_TEXT)
        if all:
            self.ccNumBox.addItem(util.ALL_TEXT)
        self.ccNumBox.currentIndexChanged.connect(self.updateValue)

        self.ccValueBox = QComboBox(self)
        for i in range(128):
            self.ccValueBox.addItem(str(i))
        if any:
            self.ccValueBox.addItem(util.ANY_TEXT)
        if all:
            self.ccValueBox.addItem(util.ALL_TEXT)
        self.ccValueBox.currentIndexChanged.connect(self.updateValue)

        self.noteNumBox = QComboBox(self)
        for i in range(128):
            self.noteNumBox.addItem('%i (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        if any:
            self.noteNumBox.addItem(util.ANY_TEXT)
        if all:
            self.noteNumBox.addItem(util.ALL_TEXT)
        self.noteNumBox.currentIndexChanged.connect(self.updateValue)

        self.noteVelBox = QComboBox(self)
        for i in range(128):
            self.noteVelBox.addItem(str(i))
        if any:
            self.noteVelBox.addItem(util.ANY_TEXT)
        if all:
            self.noteVelBox.addItem(util.ALL_TEXT)
        self.noteVelBox.currentIndexChanged.connect(self.updateValue)

        self.atNumBox = QComboBox(self)
        for i in range(128):
            self.atNumBox.addItem('%i (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        if any:
            self.atNumBox.addItem(util.ANY_TEXT)
        if all:
            self.atNumBox.addItem(util.ALL_TEXT)
        self.atNumBox.currentIndexChanged.connect(self.updateValue)

        self.atValueBox = QComboBox(self)
        for i in range(128):
            self.atValueBox.addItem(str(i))
        if any:
            self.atValueBox.addItem(util.ANY_TEXT)
        if all:
            self.atValueBox.addItem(util.ALL_TEXT)
        self.atValueBox.currentIndexChanged.connect(self.updateValue)

        # keep long boxes from expanding too far
        boxes = self.findChildren(QComboBox, '', Qt.FindDirectChildrenOnly)
        for b in boxes:
            b.setMinimumWidth(100)

        for w in [self.portBox, self.typeBox, self.channelBox]:
            w.installEventFilter(self)

        Layout = QHBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.portBox)
        Layout.addWidget(self.channelBox)
        Layout.addWidget(self.typeBox)
        Layout.addWidget(self.ccNumBox)
        Layout.addWidget(self.ccValueBox)
        Layout.addWidget(self.noteNumBox)
        Layout.addWidget(self.noteVelBox)
        Layout.addWidget(self.atNumBox)
        Layout.addWidget(self.atValueBox)
        self.setLayout(Layout)

        # init

        self.typeMap = {
            util.MSG_NOTE_ON: [ # note on
                self.noteNumBox,
                self.noteVelBox
            ],
            util.MSG_NOTE_OFF: { # note off
                self.noteNumBox
            },
            util.MSG_CC: { # cc
                self.ccNumBox,
                self.ccValueBox
            },
            util.MSG_AFTERTOUCH: { #aftertouch
                self.atNumBox,
                self.atValueBox
            }
        }
        self.clear()

    def eventFilter(self, o, e):
        if e.type() == QEvent.Wheel:
            e.ignore()
            return True
        return super().eventFilter(o, e)

    def init(self, midimessage):
        self.midimessage = midimessage
        portName = midimessage.portName
        midi = midimessage.midi
        wildcards = midimessage.wildcards

        self.block = True
        if not portName:
            portName = util.NONE_TEXT
        elif self.portBox.findText(portName) == -1:
            self.portBox.addItem(portName)
        self.portBox.setCurrentText(portName)
        if wildcards['channel']:
            if self.any:
                self.channelBox.setCurrentText(util.ANY_TEXT)
            elif self.all:
                self.channelBox.setCurrentText(uti.ALL_TEXT)
        else:
            self.channelBox.setCurrentIndex(midi.getChannel()-1)
        if midi.isNoteOn():
            iType = util.MSG_NOTE_ON
            if wildcards['noteNum']:
                if self.any:
                    self.noteNumBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.noteNumBox.setCurrentText(util.ALL_TEXT)
            else:
                self.noteNumBox.setCurrentIndex(midi.getNoteNumber())
            if wildcards['noteVel']:
                if self.any:
                    self.noteVelBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.noteVelBox.setCurrentText(util.ALL_TEXT)
            else:
                self.noteVelBox.setCurrentIndex(midi.getVelocity())
        elif midi.isNoteOff():
            iType = util.MSG_NOTE_OFF
            if wildcards['noteNum']:
                if self.any:
                    self.noteNumBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.noteNumBox.setCurrentText(util.ALL_TEXT)
            else:
                self.noteNumBox.setCurrentIndex(midi.getNoteNumber())
        elif midi.isController():
            iType = util.MSG_CC
            if wildcards['ccNum']:
                if self.any:
                    self.ccNumBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.ccNumBox.setCurrentText(util.ALL_TEXT)
            else:
                self.ccNumBox.setCurrentIndex(midi.getControllerNumber())
            if wildcards['ccValue']:
                if self.any:
                    self.ccValueBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.ccValueBox.setCurrentText(util.ALL_TEXT)
            else:
                self.ccValueBox.setCurrentIndex(midi.getControllerValue())
        elif midi.isAftertouch():
            iType = util.MSG_AFTERTOUCH
            if wildcards['atNum']:
                if self.any:
                    self.atNumBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.atNumBox.setCurrentText(util.ALL_TEXT)
            else:
                self.atNumBox.setCurrentIndex(midi.getNoteNumber())
            if wildcards['atValue']:
                if self.any:
                    self.atValueBox.setCurrentText(util.ANY_TEXT)
                elif self.all:
                    self.atValueBox.setCurrentText(util.ALL_TEXT)
            else:
                self.atValueBox.setCurrentIndex(midi.getAfterTouchValue())
        self.setType(iType)
        self.block = False

    def clear(self):
        self.setType(0)
        self.portBox.setCurrentIndex(0)
        self.channelBox.setCurrentIndex(0)
        self.typeBox.setCurrentIndex(0)
        self.noteNumBox.setCurrentIndex(0)
        self.noteVelBox.setCurrentIndex(0)
        self.ccNumBox.setCurrentIndex(0)
        self.ccValueBox.setCurrentIndex(0)
        self.atNumBox.setCurrentIndex(0)
        self.atValueBox.setCurrentIndex(0)

    def updateValue(self):
        if self.block or not self.midimessage:
            return
        channel = self.channelBox.currentIndex() + 1
        if self.typeBox.currentIndex() == 0:
            midi = MidiMessage.noteOn(channel,
                                      self.noteNumBox.currentIndex(),
                                      self.noteVelBox.currentIndex())
        if self.typeBox.currentIndex() == 1:
            midi = MidiMessage.noteOff(channel,
                                       self.noteNumBox.currentIndex())
        elif self.typeBox.currentIndex() == 2:
            midi = MidiMessage.controllerEvent(channel,
                                               self.ccNumBox.currentIndex(),
                                               self.ccValueBox.currentIndex())
        elif self.typeBox.currentIndex() == 3:
            midi = MidiMessage.aftertouchChange(channel,
                                                self.atNumBox.currentIndex(),
                                                self.atValueBox.currentIndex())
        if self.portBox.currentText() == util.NONE_TEXT:
            portName = None
        else:
            portName = self.portBox.currentText()
        self.midimessage.setWildcard('channel',
                                     self.channelBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('noteNum',
                                     self.noteNumBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('noteVel',
                                     self.noteVelBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('ccNum',
                                     self.ccNumBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('ccValue',
                                     self.ccValueBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('atNum',
                                     self.atNumBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setWildcard('atValue',
                                     self.atValueBox.currentText() in [util.ANY_TEXT, util.ALL_TEXT], emit=False)
        self.midimessage.setMidi(portName, midi)

    def setType(self, iType):
        if iType != self.typeBox.currentIndex():
            self.typeBox.setCurrentIndex(iType)
        for k, v in self.typeMap.items():
            for v2 in v:
                v2.hide()
        for w in self.typeMap[iType]:
            w.show()
        self.updateValue()

    def setPortIndex(self, iPort):
        self.portBox.setCurrentIndex(iPort)

    def addPortName(self, name):
        if self.any:
            i = self.portBox.findText(util.ANY_TEXT)
        if self.all:
            i = self.portBox.findText(util.ALL_TEXT)
        if not self.any and not self.all:
            i = self.portBox.findText(util.NONE_TEXT)
        self.portBox.insertItem(i, name)
    
    def removePortName(self, name):
        for i in range(self.portBox.count()):
            if self.portBox.itemText(i) == name:
                self.portBox.removeItem(i)
                return

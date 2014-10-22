from rtmidi import MidiMessage, RtMidiIn
from .pyqt_shim import *
#from .util import *
from . import util

class MidiEdit(QWidget):

    changed = pyqtSignal(str, MidiMessage)

    def __init__(self, parent=None, any=False, all=False, portBox=False):
        QWidget.__init__(self, parent)

        self.block = False

        self.midi = MidiMessage()

        self.portBox = QComboBox()
        self.device = RtMidiIn()
        for i in range(self.device.getPortCount()):
            portName = self.device.getPortName(i)
            self.portBox.addItem(portName)
        if any:
            self.portBox.addItem(util.ANY_TEXT)
        if all:
            self.portBox.addItem(util.ALL_TEXT)
        self.portBox.addItem(util.NONE_TEXT)
        self.portBox.setMinimumWidth(100)
        self.portBox.currentTextChanged.connect(self.setPortName)
        if not portBox:
            self.portBox.hide()

        self.channelBox = QComboBox(self)
        for i in range(1, 17):
            self.channelBox.addItem('Channel %i' % i)
        self.channelBox.currentIndexChanged.connect(self.setChannel)

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
        self.ccNumBox.currentIndexChanged.connect(self.setCCNum)

        self.ccValueBox = QComboBox(self)
        for i in range(128):
            self.ccValueBox.addItem(str(i))
        if any:
            self.ccValueBox.addItem(util.ANY_TEXT)
        self.ccValueBox.currentIndexChanged.connect(self.setCCValue)

        self.noteNumBox = QComboBox(self)
        for i in range(128):
            self.noteNumBox.addItem('%i (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        if any:
            self.noteNumBox.addItem(util.ANY_TEXT)
        self.noteNumBox.currentIndexChanged.connect(self.setNoteNum)

        self.noteVelBox = QComboBox(self)
        for i in range(128):
            self.noteVelBox.addItem(str(i))
        if any:
            self.noteVelBox.addItem(util.ANY_TEXT)
        self.noteVelBox.currentIndexChanged.connect(self.setNoteVel)

        self.atNumBox = QComboBox(self)
        for i in range(128):
            self.atNumBox.addItem('%i (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        if any:
            self.atNumBox.addItem(util.ANY_TEXT)
        self.atNumBox.currentIndexChanged.connect(self.updateAndEmit)

        self.atValueBox = QComboBox(self)
        for i in range(128):
            self.atValueBox.addItem(str(i))
        if any:
            self.atValueBox.addItem(util.ANY_TEXT)
        self.atValueBox.currentIndexChanged.connect(self.updateAndEmit)

        # keep long boxes from expanding too far
        boxes = self.findChildren(QComboBox, '', Qt.FindDirectChildrenOnly)
        for b in boxes:
            b.setMinimumWidth(100)

        Layout = QHBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        if portBox:
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

        self.setType(0)

    def init(self, portName, midi):
        self.block = True
        if not portName:
            portName = util.NONE_TEXT
        elif self.portBox.findText(portName) == -1:
            self.portBox.addItem(portName)
        self.portBox.setCurrentText(portName)
        self.channelBox.setCurrentIndex(midi.getChannel()-1)
        if midi.isNoteOn():
            iType = util.MSG_NOTE_ON
            self.noteNumBox.setCurrentIndex(midi.getNoteNumber())
            self.noteVelBox.setCurrentIndex(midi.getVelocity())
        elif midi.isNoteOff():
            iType = util.MSG_NOTE_OFF
            self.noteNumBox.setCurrentIndex(midi.getNoteNumber())
        elif midi.isController():
            iType = util.MSG_CC
            self.ccNumBox.setCurrentIndex(midi.getControllerNumber())
            self.ccValueBox.setCurrentIndex(midi.getControllerValue())
        elif midi.isAftertouch():
            iType = util.MSG_AFTERTOUCH
            self.atNumBox.setCurrentIndex(midi.getNoteNumber())
            self.atValueBox.setCurrentIndex(midi.getAfterTouchValue())
        self.setType(iType)
        self.block = False

    def clear(self):
        self.portBox.setCurrentIndex(0)
        self.channelBox.setCurrentIndex(0)
        self.typeBox.setCurrentIndex(0)
        self.noteNumBox.setCurrentIndex(0)
        self.noteVelBox.setCurrentIndex(0)
        self.ccNumBox.setCurrentIndex(0)
        self.ccValueBox.setCurrentIndex(0)
        self.atNumBox.setCurrentIndex(0)
        self.atValueBox.setCurrentIndex(0)

    def updateAndEmit(self):
        if self.block:
            return
        channel = self.channelBox.currentIndex() + 1
        if self.typeBox.currentIndex() == 0:
            self.midi = MidiMessage.noteOn(channel,
                                           self.noteNumBox.currentIndex(),
                                           self.noteVelBox.currentIndex())
        if self.typeBox.currentIndex() == 1:
            self.midi = MidiMessage.noteOff(channel,
                                            self.noteNumBox.currentIndex())
        elif self.typeBox.currentIndex() == 2:
            self.midi = MidiMessage.controllerEvent(channel,
                                                    self.ccNumBox.currentIndex(),
                                                    self.ccValueBox.currentIndex())
        elif self.typeBox.currentIndex() == 3:
            self.midi = MidiMessage.aftertouchChange(channel,
                                                     self.atNumBox.currentIndex(),
                                                     self.atValueBox.currentIndex())
        if self.portBox.currentText() == util.NONE_TEXT:
            portName = None
        else:
            portName = self.portBox.currentText()
        self.changed.emit(portName, self.midi)

    def setChannel(self, x):
        if x != self.channelBox.currentIndex():
            self.channelBox.setCurrentIndex(x-1)
        self.updateAndEmit()

    def setPortName(self, x):
        if x != self.portBox.currentText():
            self.portBox.setCurrentText(x)
        self.updateAndEmit()

    def setType(self, iType):
        if iType != self.typeBox.currentIndex():
            self.typeBox.setCurrentIndex(iType)
        for k, v in self.typeMap.items():
            for v2 in v:
                v2.hide()
        for w in self.typeMap[iType]:
            w.show()
        self.updateAndEmit()

    def setCCNum(self, x):
        if x != self.ccNumBox.currentIndex():
            self.ccNumBox.setCurrentIndex(x)
        self.updateAndEmit()

    def setCCValue(self, x):
        if x != self.ccValueBox.currentIndex():
            self.ccValueBox.setCurrentIndex(x)
        self.updateAndEmit()

    def setNoteNum(self, x):
        if x != self.noteNumBox.currentIndex():
            self.noteNumBox.setCurrentIndex(x)
        self.updateAndEmit()

    def setNoteVel(self, x):
        if x != self.noteVelBox.currentIndex():
            self.noteVelBox.setCurrentIndex(x)
        self.updateAndEmit()

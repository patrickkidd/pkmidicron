import rtmidi
from .pyqt_shim import *
#from .util import *
from . import util
from .midiedit import MidiEdit
from .ports import outputs
CRAZY_INTERVAL = 10


class Simulator(QWidget):

    received = pyqtSignal(str, rtmidi.MidiMessage)
    changed = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self._timer = 0
        self.randomout = rtmidi.RandomOut()
        self.simulator = None
        self.image = QImage(":/box-bg-1.jpg")

        self.fakeBox = QCheckBox("Route Internally", self)
        self.fakeBox.setToolTip("Don't send through hardware, just route within the app.")

        self.crazyBox = QCheckBox("Go Crazy", self)
        self.crazyBox.stateChanged[int].connect(self.goCrazy)
        self.crazyBox.setToolTip("Spastically spew tons and tons of random messages.")

        self.midiEdit = MidiEdit(self, portBox=True, all=True, input=False)
        # all this just to pass that 'all' param. ugh..
        trim = [
            self.midiEdit.channelBox,
            self.midiEdit.typeBox,
            self.midiEdit.noteNumBox,
            self.midiEdit.noteVelBox,
            self.midiEdit.ccNumBox,
            self.midiEdit.ccValueBox,
            self.midiEdit.atNumBox,
            self.midiEdit.atValueBox,
        ]
        for w in trim:
            w.removeItem(w.count()-1)
        self.all = True

        self.sendButton = QPushButton("&Send", self)
        self.sendButton.clicked.connect(self.send)

        LowerLayout = QHBoxLayout()
        LowerLayout.addWidget(self.fakeBox)
        LowerLayout.addWidget(self.crazyBox)
        LowerLayout.addStretch(1)
        LowerLayout.addWidget(self.sendButton)
        Layout = QVBoxLayout()
        Layout.addStretch(1)
        Layout.addWidget(self.midiEdit)
        Layout.addLayout(LowerLayout)
        Layout.addStretch(1)
        self.setLayout(Layout)

    def paintEvent(self, e):
        e.accept()
        p = QPainter(self)
        p.setBrush(QBrush(self.image))
        p.setPen(QColor('#b6b6b6'))
        rect = self.rect()
        rect.setWidth(rect.width()-1)
        rect.setHeight(rect.height()-1)
        p.drawRoundedRect(rect, 5, 5)

    def init(self, simulator):
        self.simulator = simulator
        self.midiEdit.init(simulator)
        if self.midiEdit.portName == util.NONE_TEXT:
            self.midiEdit.setPortIndex(0)

    def clear(self):
        self.midiEdit.clear()
        self.simulator = None
        
    def send(self, msg=None):
        def _sendToOnePort(portName, m):
            if self.fakeBox.isChecked():
                self.received.emit(portName, m)
            else:
                outputs().sendMessage(portName, m)
        if msg is None or type(msg) == bool:
            msg = self.simulator.getMidi()
        if self.simulator.portName == util.ALL_TEXT:
            for portName in outputs().names():
                _sendToOnePort(portName, msg)
        else:
            _sendToOnePort(self.simulator.portName, msg)

    def goCrazy(self, on):
        if self._timer:
            self.killTimer(self._timer)
            self._timer = 0
        if on:
            self._timer = self.startTimer(CRAZY_INTERVAL)

    def timerEvent(self, e):
        msg = self.randomout.get()
        self.send(msg)

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

import rtmidi
from .pyqt_shim import *
#from .util import *
from . import util
from .midiedit import MidiEdit

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

        self.crazyBox = QCheckBox("Go Crazy", self)
        self.crazyBox.stateChanged[int].connect(self.goCrazy)

        self.fakeBox = QCheckBox("Fake", self)
        self.fakeBox.setFixedWidth(70)
        self.fakeBox.setToolTip("Don't send through hardware, just route internally.")

        self.devices = {}
        self.device = rtmidi.RtMidiOut()
        for i in range(self.device.getPortCount()):
            portName = self.device.getPortName(i)
            dev = rtmidi.RtMidiOut()
            dev.openPort(i)
            self.devices[portName] = dev

        self.midiEdit = MidiEdit(self, portBox=True, all=True)

        self.sendButton = QPushButton("&Send", self)
        self.sendButton.clicked.connect(self.send)

        LowerLayout = QHBoxLayout()
        LowerLayout.addWidget(self.crazyBox)
        LowerLayout.addWidget(self.fakeBox)
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
        def _send(portName, m):
            if not portName:
                return
            if self.fakeBox.isChecked():
                self.received.emit(portName, m)
            else:
                self.devices[portName].sendMessage(m)
        if msg is None or type(msg) == bool:
            msg = self.simulator.midi
        if self.simulator.portName == util.ALL_TEXT:
            for portName, v in self.devices.items():
                _send(portName, msg)
        else:
            _send(self.simulator.portName, msg)

    def goCrazy(self, on):
        if self._timer:
            self.killTimer(self._timer)
            self._timer = 0
        if on:
            self._timer = self.startTimer(CRAZY_INTERVAL)

    def timerEvent(self, e):
        msg = self.randomout.get()
        self.send(msg)

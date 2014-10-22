import rtmidi
from .pyqt_shim import *
from .util import *
from .midiedit import MidiEdit

CRAZY_INTERVAL = 10


class Simulator(QWidget):

    received = pyqtSignal(str, rtmidi.MidiMessage)
    changed = pyqtSignal()

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setFixedHeight(70)

        self._timer = 0
        self.randomout = rtmidi.RandomOut()

        self.crazyBox = QCheckBox("Go Crazy", self)
        self.crazyBox.stateChanged[int].connect(self.goCrazy)

        self.fakeBox = QCheckBox("Fake", self)
        self.fakeBox.setFixedWidth(70)
        self.fakeBox.setToolTip("Don't send through hardware, just route internally.")

        self.devices = {}
        self.device = rtmidi.RtMidiOut()
        self.portBox = QComboBox(self)
        for i in range(self.device.getPortCount()):
            portName = self.device.getPortName(i)
            self.portBox.addItem(portName)
            dev = rtmidi.RtMidiOut()
            dev.openPort(i)
            self.devices[portName] = dev
        self.portBox.addItem(ALL_TEXT)
        self.portBox.setMinimumWidth(100)

        self.midiEdit = MidiEdit(self)
        self.midiEdit.changed.connect(self.setValue)

        self.sendButton = QPushButton("&Send", self)
        self.sendButton.clicked.connect(self.send)

        UpperLayout = QHBoxLayout()
        UpperLayout.addWidget(self.portBox)
        UpperLayout.addWidget(self.midiEdit)
        UpperLayout.addStretch(1)
        LowerLayout = QHBoxLayout()
        LowerLayout.addWidget(self.crazyBox)
        LowerLayout.addWidget(self.fakeBox)
        LowerLayout.addStretch(1)
        LowerLayout.addWidget(self.sendButton)
        Layout = QVBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        Layout.addStretch(1)
        Layout.addLayout(UpperLayout)
        Layout.addLayout(LowerLayout)
        Layout.addStretch(1)
        self.setLayout(Layout)

    def init(self, simulator):
        self.simulator = simulator
        self.midiEdit.init(simulator.portName, simulator.midi)

    def clear(self):
        self.midiEdit.clear()
        self.simulator = None
        
    def setValue(self, portName, midi):
        self.simulator.setMidi(portName, midi)

    def send(self, msg=None):
        def _send(portName, m):
            if self.fakeBox.isChecked():
                self.received.emit(portName, m)
            else:
                self.devices[portName].sendMessage(m)
        if msg is None or type(msg) == bool:
            msg = self.simulator.midi
        if self.portBox.currentText() == ALL_TEXT:
            for portName, v in self.devices.items():
                _send(portName, msg)
        else:
            _send(self.portBox.currentText(), msg)

    def goCrazy(self, on):
        if self._timer:
            self.killTimer(self._timer)
            self._timer = 0
        if on:
            self._timer = self.startTimer(CRAZY_INTERVAL)

    def timerEvent(self, e):
        msg = self.randomout.get()
        self.send(msg)
            

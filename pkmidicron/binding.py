import os
from rtmidi import *
from .pyqt_shim import *
from .util import *
from .midiedit import MidiEdit


class Binding(QFrame):

    changed = pyqtSignal()
    removeMe = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameStyle(QFrame.Panel)
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)

        ## front panel

        self.frontWidget = QWidget(self)

        self.nameEdit = QLineEdit(self.frontWidget)
        self.nameEdit.setFixedWidth(150)

        self.summaryLabel = QLabel(self)
        self.summaryLabel.setMinimumWidth(100)

        self.activityLED = Led(self.frontWidget)

        self.expandButton = QPushButton(">>>", self.frontWidget)
        self.expandButton.setMaximumSize(50, 50)
        self.expandButton.clicked.connect(self.toggleDetails)

        self.removeButton = QPushButton("-", self.frontWidget)
        self.removeButton.setMaximumSize(50, 50)
        self.removeButton.clicked.connect(self._removeMe)

        ## details panel

        self.detailsWidget = QWidget(self)

        self.device = rtmidi.RtMidiIn()
        self.portBox = QComboBox(self)
        for i in range(self.device.getPortCount()):
            self.portBox.addItem(self.device.getPortName(i))
        self.portBox.addItem(ANY_TEXT)
        self.portBox.currentIndexChanged[int].connect(self.updateSummary)

        self.midiEdit = MidiEdit(self, any=True)

        self.openCheckBox = QCheckBox('Open', self)

        self.cmdEdit = QLineEdit(self.detailsWidget)
        self.cmdEdit.setMinimumWidth(150)
        self.cmdEdit.textChanged[str].connect(self.setCmd)

        self.findButton = QPushButton("...", self.detailsWidget)
        self.findButton.setMaximumSize(50, 50)
        self.findButton.clicked.connect(self.findCommand)

        Layout = QVBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        self.setLayout(Layout)

        self.frontLayout = QHBoxLayout()
        self.frontLayout.setContentsMargins(0, 0, 0, 0)
        self.frontLayout.addWidget(self.activityLED, 0)
        self.frontLayout.addWidget(self.nameEdit, 0)
        self.frontLayout.addWidget(self.summaryLabel, 1)
        self.frontLayout.addWidget(self.expandButton, 0)
        self.frontLayout.addWidget(self.removeButton, 0)
        self.frontWidget.setLayout(self.frontLayout)
        Layout.addWidget(self.frontWidget)

        self.detailsLayout = QVBoxLayout()
        self.detailsLayout.setContentsMargins(0, 0, 0, 0)
        self.detailsLayout.setSpacing(0)
        self.detailsWidget.setLayout(self.detailsLayout)
        DetailsMidi = QHBoxLayout()
        DetailsMidi.setSpacing(10)
        self.detailsLayout.addLayout(DetailsMidi)
        DetailsMidi.addWidget(self.portBox)
        DetailsMidi.addWidget(self.midiEdit)
        DetailsMidi.addStretch(5)
        DetailsCmd = QHBoxLayout()
        DetailsCmd.setSpacing(10)
        self.detailsLayout.addLayout(DetailsCmd)
        DetailsCmd.addWidget(self.openCheckBox)        
        DetailsCmd.addWidget(self.cmdEdit)
        DetailsCmd.addWidget(self.findButton)
        Layout.addWidget(self.detailsWidget)

        # init

        self.expanded = True
        self.midiEdit.changed.connect(self.updateSummary)
        self.updateSummary(self.midiEdit.midi)


    def mouseDoubleClickEvent(self, e):
        self.toggleDetails()
    
    def readPatch(self, patch):
        portName = patch.value('portName', type=str)
        if self.portBox.findText(portName) == -1:
            self.portBox.addItem(portName)
        self.portBox.setCurrentText(portName)
        self.setCmd(patch.value('cmd', type=str))
        self.nameEdit.setText(patch.value('name', type=str))
        self.openCheckBox.setChecked(patch.value('open', type=bool))
        self.setExpanded(patch.value('expanded', type=bool))
        self.midiEdit.readPatch(patch)

    def writePatch(self, patch):
        patch.setValue('portName', self.portBox.currentText())
        patch.setValue('cmd', self.cmdEdit.text())
        patch.setValue('name', self.nameEdit.text())
        patch.setValue('open', self.openCheckBox.isChecked())
        patch.setValue('expanded', self.expanded)
        self.midiEdit.writePatch(patch)

    def _removeMe(self):
        self.removeMe.emit(self)

    def toggleDetails(self):
        self.setExpanded(not self.expanded)

    def setExpanded(self, on):
        if on:
            self.detailsWidget.show()
            setBackgroundColor(self, QColor(Qt.lightGray).lighter(115))
        else:
            self.detailsWidget.hide()
            clearBackgroundColor(self)
        self.expanded = on

    def setCmd(self, text):
        if text != self.cmdEdit.text():
            self.cmdEdit.setText(text)
        self.changed.emit()

    def updateSummary(self, midi=None):
        if midi is None:
            midi = self.midiEdit.midi
        summary = '%s: %s' % (self.portBox.currentText(), str(self.midiEdit.midi))
        self.summaryLabel.setText(summary)
        self.changed.emit()


    def findCommand(self):
        ret = QFileDialog.getOpenFileName(self, "Open Program",
                                          "",
                                          "All Files (*.*)")
        if ret[0]:
            self.setCmd(ret[0])

    def match(self, portName, m):
        if self.portBox.currentText() != ANY_TEXT and portName != self.portBox.currentText():
            return

        m1 = MidiMessage(m)
        m2 = MidiMessage(self.midiEdit.midi)

        if m2.isNoteOn() or m2.isNoteOff():
            if self.midiEdit.noteNumBox.currentText() == ANY_TEXT:
                m2.setNoteNumber(m1.getNoteNumber())
            if m2.isNoteOn() and self.midiEdit.noteVelBox.currentText() == ANY_TEXT:
                m2.setVelocity(m1.getVelocity() / 127.0)
        elif m2.isController():
            if self.midiEdit.ccNumBox.currentText() == ANY_TEXT:
                m2 = MidiMessage.controllerEvent(m2.getChannel(),
                                                 m1.getControllerNumber(),
                                                 m2.getControllerValue())
            if self.midiEdit.ccValueBox.currentText() == ANY_TEXT:
                m2 = MidiMessage.controllerEvent(m2.getChannel(),
                                                 m2.getControllerNumber(),
                                                 m1.getControllerValue())

        elif m2.isAftertouch():
            if self.midiEdit.atNumBox.currentText() == ANY_TEXT:
                m2 = MidiMessage.aftertouchChange(m2.getChannel(),
                                                  m1.getNoteNumber(),
                                                  m2.getAfterTouchValue())
            if self.midiEdit.atValueBox.currentText() == ANY_TEXT:
                m2 = MidiMessage.aftertouchChange(m2.getChannel(),
                                                  m2.getNoteNumber(),
                                                  m1.getAfterTouchValue())

        if m1 == m2:
            self.activityLED.flash()
            cmd = self.cmdEdit.text()
            if self.openCheckBox.isChecked():
                if os.name == 'posix':
                    cmd = 'open ' + cmd
                else:
                    cmd = 'start ' + cmd
            if cmd:
                os.system(cmd)



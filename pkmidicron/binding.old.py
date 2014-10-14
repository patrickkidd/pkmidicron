import os
from pyqt_shim import *
from rtmidi import *
from .util import *



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
        self.nameEdit.setMinimumWidth(150)

        self.summaryLabel = QLabel(self)
        self.summaryLabel.setMinimumWidth(300)

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

        self.midiEdit = MessageEdit(self)

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
        self.frontWidget.setLayout(self.frontLayout)
        self.frontLayout.addWidget(self.activityLED)
        self.frontLayout.addWidget(self.nameEdit)
        self.frontLayout.addWidget(self.summaryLabel)
        self.frontLayout.addWidget(self.expandButton)
        self.frontLayout.addWidget(self.removeButton)
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
        self.midiEdit.changed.connect(self._onChanged)
        self._onChanged(self.midiEdit.midi)
    
    def readSettings(self, settings):
        portName = settings.value('portName', type=str)
        if self.portBox.findText(portName) == -1:
            self.portBox.addItem(portName)
        self.portBox.setCurrentText(portName)
        self.setCmd(settings.value('cmd', type=str))
        self.nameEdit.setText(settings.value('name', type=str))
        self.openCheckBox.setChecked(settings.value('open', type=bool))
        self.setExpanded(settings.value('expanded', type=bool))
        self.midiEdit.readSettings(settings)

    def writeSettings(self, settings):        
        settings.setValue('portName', self.portBox.currentText())
        settings.setValue('cmd', self.cmdEdit.text())
        settings.setValue('name', self.nameEdit.text())
        settings.setValue('open', self.openCheckBox.isChecked())
        settings.setValue('expanded', self.expanded)
        self.midiEdit.writeSettings(settings)

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

    def _onChanged(self, midi):
        self.summaryLabel.setText(str(self.midiEdit.midi))


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
        m2 = MidiMessage(self.midi)

        if m2.isNoteOn():
            if self.noteNumBox.currentText() == ANY_TEXT:
                m2.setNoteNumber(m1.getNoteNumber())
            if self.noteVelBox.currentText() == ANY_TEXT:
                m2.setVelocity(m1.getVelocity() / 127.0)
        elif m2.isController():
            if self.ccNumBox.currentText() == ANY_TEXT:
                m2.setControllerNumber(m1.getControllerNumber())
            if self.ccValueBox.currentText() == ANY_TEXT:
                m2.setControllerValue(m1.getControllerValue())

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



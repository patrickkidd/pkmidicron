import os
from pyqt_shim import *
from rtmidi import *
import util


class Binding(QFrame):

    changed = pyqtSignal()
    removeMe = pyqtSignal(QWidget)

    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        self.setFrameStyle(QFrame.Panel)

        self.midi = MidiMessage()

        ## front panel

        self.frontWidget = QWidget(self)

        self.nameEdit = QLineEdit(self.frontWidget)
        self.nameEdit.setMinimumWidth(150)

        self.summaryLabel = QLabel(self)
        self.summaryLabel.setMinimumWidth(300)

        self.activityLED = util.Led(self.frontWidget)

        self.expandButton = QPushButton(">>>", self.frontWidget)
        self.expandButton.setMaximumSize(50, 50)
        self.expandButton.clicked.connect(self.toggleDetails)

        self.removeButton = QPushButton("-", self.frontWidget)
        self.removeButton.setMaximumSize(50, 50)
        self.removeButton.clicked.connect(self._removeMe)

        ## details panel

        self.detailsWidget = QWidget(self)

        self.typeBox = QComboBox(self.detailsWidget)
        self.typeBox.addItem("Note")
        self.typeBox.addItem("CC")
        self.typeBox.currentIndexChanged.connect(self.setType)

        self.ccNumBox = QComboBox(self.detailsWidget)
        for i in range(128):
            name = MidiMessage.getControllerName(i)
            if name:
                name = ': (%s)' % name
            self.ccNumBox.addItem('%i %s' % (i, name))
        self.ccNumBox.currentIndexChanged.connect(self.setCCNum)

        self.ccValueBox = QComboBox(self.detailsWidget)
        for i in range(128):
            self.ccValueBox.addItem(str(i))
        self.ccValueBox.currentIndexChanged.connect(self.setCCValue)

        self.noteNumBox = QComboBox(self.detailsWidget)
        for i in range(128):
            self.noteNumBox.addItem('%i : (%s)' % (i, MidiMessage.getMidiNoteName(i)))
        self.noteNumBox.currentIndexChanged.connect(self.setNoteNum)

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
        DetailsMidi.addWidget(self.typeBox)
        DetailsMidi.addWidget(self.noteNumBox)
        DetailsMidi.addWidget(self.ccNumBox)
        DetailsMidi.addWidget(self.ccValueBox)
        DetailsMidi.addStretch(5)
        DetailsCmd = QHBoxLayout()
        DetailsCmd.setSpacing(10)
        self.detailsLayout.addLayout(DetailsCmd)
        DetailsCmd.addWidget(self.openCheckBox)        
        DetailsCmd.addWidget(self.cmdEdit)
        DetailsCmd.addWidget(self.findButton)
        Layout.addWidget(self.detailsWidget)

        # init

        self.changed.connect(self._onChanged)
        self.typeMap = {
            'all': [
                self.noteNumBox,
                self.ccNumBox,
                self.ccValueBox
            ],
            0: [ # note
                self.noteNumBox
            ],
            1: { # cc
                self.ccNumBox,
                self.ccValueBox
            }
        }
        self.setType(0)
        self.expanded = True
        self._onChanged()

    
    def readSettings(self, settings):
        self.setType(settings.value('type', type=int))
        self.setNoteNum(settings.value('noteNum', type=int))
        self.setCCNum(settings.value('ccNum', type=int))
        self.setCCValue(settings.value('ccValue', type=int))
        self.setCmd(settings.value('cmd', type=str))
        self.nameEdit.setText(settings.value('name', type=str))
        self.openCheckBox.setChecked(settings.value('open', type=bool))
        self.setExpanded(settings.value('expanded', type=bool))

    def writeSettings(self, settings):
        settings.setValue('type', self.typeBox.currentIndex())
        settings.setValue('noteNum', self.noteNumBox.currentIndex())
        settings.setValue('ccNum', self.ccNumBox.currentIndex())
        settings.setValue('ccValue', self.ccValueBox.currentIndex())
        settings.setValue('cmd', self.cmdEdit.text())
        settings.setValue('name', self.nameEdit.text())
        settings.setValue('open', self.openCheckBox.isChecked())
        settings.setValue('expanded', self.expanded)

    def _removeMe(self):
        self.removeMe.emit(self)

    def toggleDetails(self):
        self.setExpanded(not self.expanded)

    def setExpanded(self, on):
        if on:
            self.detailsWidget.show()
            util.setBackgroundColor(self, QColor(Qt.lightGray).lighter(115))
        else:
            self.detailsWidget.hide()
            util.clearBackgroundColor(self)
        self.expanded = on

    def setType(self, iType):
        #if iType == self.typeBox.currentIndex():
        self.typeBox.setCurrentIndex(iType)
        for w in self.typeMap['all']:
            w.hide()
        for w in self.typeMap[iType]:
            w.show()
        self.changed.emit()

    def setCCNum(self, x):
        if x == self.ccNumBox.currentIndex():
            return
        self.ccNumBox.setCurrentIndex(x)
        self.changed.emit()

    def setCCValue(self, x):
        if x == self.ccValueBox.currentIndex():
            return
        self.ccValueBox.setCurrentIndex(x)
        self.changed.emit()

    def setNoteNum(self, x):
        if x == self.noteNumBox.currentIndex():
            return
        self.noteNumBox.setCurrentIndex(x)
        self.changed.emit()

    def setCmd(self, text):
        if text == self.cmdEdit.text():
            return
        self.cmdEdit.setText(text)
        self.changed.emit()

    def _onChanged(self):
        if self.typeBox.currentIndex() == 0:
            self.midi = MidiMessage.noteOn(1,
                                           self.noteNumBox.currentIndex(), 100)
        elif self.typeBox.currentIndex() == 1:
            self.midi = MidiMessage.controllerEvent(1,
                                                    self.ccNumBox.currentIndex(),
                                                    self.ccValueBox.currentIndex())
        self.summaryLabel.setText(str(self.midi))


    def findCommand(self):
        ret = QFileDialog.getOpenFileName(self, "Open Program",
                                          "",
                                          "All Files (*.*)")
        if ret[0]:
            self.setCmd(ret[0])

    def match(self, m):
        if m.isNoteOn(): # note mode
            m.setVelocity(100 / 127.0)
        if m == self.midi:
            self.activityLED.flash()
            cmd = self.cmdEdit.text()
            if self.openCheckBox.isChecked():
                if os.name == 'posix':
                    cmd = 'open ' + cmd
                else:
                    cmd = 'start ' + cmd
            if cmd:
                os.system(cmd)



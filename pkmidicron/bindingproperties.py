from .pyqt_shim import *
from . import util, midiedit
import rtmidi


class CriteriaBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, tr('Match Criteria'), parent)

        self.midiEdit = midiedit.MidiEdit(self.content, portBox=True, any=True)
        self.midiEdit.changed[str, rtmidi.MidiMessage].connect(self.setValue)

        Layout = QHBoxLayout()
        Layout.addWidget(self.midiEdit)
        Layout.addSpacing(1)
        self.content.setLayout(Layout)

    def init(self, binding):
        self.binding = binding
        self.criteria = binding.criteria[0]
        self.midiEdit.init(self.criteria.portName, self.criteria.midi)

    def clear(self):
        self.binding = None
        self.criteria = None

    def setValue(self, portName, midi):
        self.criteria.setMidi(portName, midi)


class ActionWidget(QFrame):

    clicked = pyqtSignal(QFrame)
    removeMe = pyqtSignal(QFrame)

    def __init__(self, action, title, parent=None):
        QFrame.__init__(self, parent)

        self.action = action

        self.titleLabel = QLabel(title, self)
        self.removeButton = QPushButton('-', self)
        self.removeButton.clicked.connect(self._removeMe)

        UpperLayout = QHBoxLayout()
        UpperLayout.addWidget(self.titleLabel)
        UpperLayout.addStretch(1)
        UpperLayout.addWidget(self.removeButton)
        Layout = QVBoxLayout()
        Layout.addLayout(UpperLayout)
        Layout.addSpacing(1)
        self.setLayout(Layout)

    def mouseReleaseEvent(self, e):
        self.clicked.emit(self)

    def _removeMe(self):
        self.removeMe.emit(self)

    def init(self, action):
        self.action = action

    def clear(self):
        self.action = None


class SendMessageAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr('Send Message'), parent)

        self.midiEdit = midiedit.MidiEdit(self, portBox=True)
        self.midiEdit.changed.connect(self.setStuff)
        self.layout().addWidget(self.midiEdit)

    def init(self, action):
        super().init(action)
        self.midiEdit.init(action.midiMessage.portName, action.midiMessage.midi)

    def setStuff(self, portName, midi):
        self.action.midiMessage.setMidi(portName, midi)


class RunProgramAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Run Program"), parent)

        self.cmdEdit = QLineEdit(self)
        self.cmdEdit.textChanged.connect(self.setCmd)
        self.layout().addWidget(self.cmdEdit)

    def init(self, action):
        super().init(action)
        self.cmdEdit.setText(action.text)

    def setCmd(self, x):
        self.action.text = x        


class OpenFileAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Open File"), parent)

        self.cmdEdit = QLineEdit(self)
        self.cmdEdit.textChanged.connect(self.setCmd)
        self.layout().addWidget(self.cmdEdit)

    def init(self, action):
        super().init(action)
        self.cmdEdit.setText(action.text)

    def setCmd(self, x):
        self.action.text = x

        

class ActionBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, tr('Action'), parent)

        self.widgets = []

        self.addBox = QComboBox(self)
        self.addBox.addItem('Send message')
        self.addBox.addItem('Run Program')
        self.addBox.addItem('Open File')
        self.addBox.activated.connect(self.addAction)

        self.actionsLayout = QVBoxLayout()
        Layout = QVBoxLayout()
        Layout.addWidget(self.addBox)
        Layout.addLayout(self.actionsLayout)
        self.content.setLayout(Layout)

    def init(self, binding):
        self.clear()
        self.binding = binding
        for action in self.binding.actions:
            self.addAction(action)

    def clear(self):
        for w in list(self.widgets):
            self.actionsLayout.removeWidget(w)
            self.widgets.remove(w)
            w.clear() # delete refs
            w.setParent(None)
        self.binding = None

    def addAction(self, x):
        if type(x) == int:
            action = self.binding.addAction(x)
            iType = x
        else:
            iType = x.type
            action = x
        if iType == util.ACTION_SEND_MESSAGE:
            widget = SendMessageAction(action, self)
        elif iType == util.ACTION_RUN_PROGRAM:
            widget = RunProgramAction(action, self)
        elif iType == util.ACTION_OPEN_FILE:
            widget = OpenFileAction(action, self)
        self.actionsLayout.addWidget(widget)
#        widget.clicked.connect(self.setSelectedAction)
        widget.removeMe.connect(self.removeAction)
        widget.init(action)
        self.widgets.append(widget)

    def removeAction(self, widget):
        action = widget.action
        self.binding.removeAction(action)
        self.actionsLayout.removeWidget(widget)
        self.widgets.remove(widget)
        widget.setParent(None)

    def setSelectedAction(self, widget):
        """ doesn't work yet """
        for w in self.widgets:
            if w != action:
                w.setProperty('selected', False)
        if widget:
            widget.setProperty('selected', True)


class BindingProperties(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.criteriaBox = CriteriaBox(self)
        self.hr1 = util.HR(self)
        self.actionBox = ActionBox(self)

        Layout = QVBoxLayout(self)
        Layout.addWidget(self.criteriaBox)
        Layout.addWidget(self.hr1)
        Layout.addWidget(self.actionBox)
        Layout.addStretch(10)
        self.setLayout(Layout)

        # init

        self.clear()
        
    def init(self, binding):
        self.criteriaBox.init(binding)
        self.actionBox.init(binding)
        self.criteriaBox.show()
        self.actionBox.show()

    def clear(self):
        self.criteriaBox.hide()
        self.criteriaBox.clear()
        self.actionBox.hide()
        self.actionBox.clear()

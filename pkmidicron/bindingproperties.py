from .pyqt_shim import *
from . import util, midiedit, scripteditor
import rtmidi


class CriteriaBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, QPixmap(':/Criteria.png'), parent)

        self.midiEdit = midiedit.MidiEdit(self.content, portBox=True, any=True)

        Layout = QHBoxLayout()
        Layout.addWidget(self.midiEdit)
        Layout.addSpacing(1)
        self.content.setLayout(Layout)

    def init(self, binding):
        self.binding = binding
        self.criteria = binding.criteria[0]
        self.midiEdit.init(self.criteria)

    def clear(self):
        self.binding = None
        self.criteria = None


class ActionWidget(QFrame):

    clicked = pyqtSignal(QFrame)
    removeMe = pyqtSignal(QFrame)

    def __init__(self, action, title, parent=None):
        QFrame.__init__(self, parent)

        self.action = action

        self.titleLabel = QLabel(title, self)
        self.removeButton = util.Button(self)
        self.removeButton.clicked.connect(self._removeMe)
        self.removeButton.setFixedSize(30, 30)
        self.removeButton.setIcon(QIcon(QPixmap(":/icons/retina/multiply.png")))
        self.removeButton.setStyleSheet("""
Button {
    background: transparent;
}
Button:hover {
        background: rgba(255, 50, 50, .5);
    border-radius: 3px;
}
Button:pressed {
    margin: 1px;
    border: 1px solid lightGrey;
    border-radius: 5px;
    background: rgba(255, 50, 50, .7);
}
        """)

        UpperLayout = QHBoxLayout()
        UpperLayout.addWidget(self.titleLabel)
        UpperLayout.addStretch(1)
        UpperLayout.addWidget(self.removeButton)
        Layout = QVBoxLayout()
        Layout.addLayout(UpperLayout)
        Layout.addSpacing(1)
        self.setLayout(Layout)

    def paintEvent(self, e):
        e.accept()
        p = QPainter(self)
        p.setPen(QColor('#b6b6b6'))
        p.setBrush(Qt.transparent)
        p.drawRect(self.rect().adjusted(0, 0, -1, -1))

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

        self.forwardBox = QCheckBox('Forward', self)
        self.forwardBox.setChecked(action.forward)
        self.forwardBox.stateChanged.connect(self.setForward)

        self.layout().addWidget(self.forwardBox)
        self.layout().addWidget(self.midiEdit)

    def init(self, action):
        super().init(action)
        self.midiEdit.init(action.midiMessage)

    def setForward(self, x):
        self.action.setForward(x == Qt.Checked)


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


class RunScriptAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Run Script"), parent)

        self.editButton = QPushButton(tr('Edit'), self)
        self.editButton.clicked.connect(self.showEditor)

        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(self.testScript)

        self.editButton.setFixedWidth(100)
        self.testButton.setFixedWidth(100)

        Layout = QHBoxLayout()
        Layout.addWidget(self.editButton)
        Layout.addSpacing(10)
        Layout.addWidget(self.testButton)

        self.saveTimer = QTimer(self)
        self.saveTimer.timeout.connect(self.save)
        self.saveTimer.setSingleShot(True)

        if action.editor:
            self._initEditor(action.editor)

        self.layout().addLayout(Layout)

    def init(self, action):
        super().init(action)

    def _initEditor(self, editor):
        editor.closed.connect(self.onEditorClosed)
        editor.textChanged.connect(self.onTextChanged)

    def showEditor(self):
        if not self.action.editor:
            self.action.editor = scripteditor.ScriptEditor()
            self.action.editor.setText(self.action.source)
            self._initEditor(self.action.editor)
        self.action.editor.show()
        self.action.editor.raise_()

    def onTextChanged(self):
        self.saveTimer.start(100) # bounce

    def testScript(self):
        midi = rtmidi.MidiMessage.noteOn(1, 100, 100)
        self.action.trigger(midi)

    def save(self):
        if self.action.editor.dirty:
            text = self.action.editor.text()
            self.action.setSource(text)
            self.action.editor.setDirty(False)
        
    def onEditorClosed(self):
        self.save()
        

class ActionBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, QPixmap(':/Actions.png'), parent)

        self.widgets = []

        self.addBox = QComboBox(self)
        self.addBox.addItem('Send message')
        self.addBox.addItem('Run Program')
        self.addBox.addItem('Open File')
        self.addBox.addItem('Run Script')
        self.addBox.activated.connect(self.addAction)

        self.addBox.installEventFilter(self)

        self.actionsLayout = QVBoxLayout()
        Layout = QVBoxLayout()
        Layout.addWidget(self.addBox)
        Layout.addLayout(self.actionsLayout)
        self.content.setLayout(Layout)

    def eventFilter(self, o, e):
        if e.type() == QEvent.Wheel:
            e.ignore()
            return True
        return super().eventFilter(o, e)

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
        elif iType == util.ACTION_RUN_SCRIPT:
            widget = RunScriptAction(action, self)
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
        super().__init__(parent)

        self.binding = None
        self.criteriaBox = CriteriaBox(self)
        self.hr1 = util.HR(self)
        self.actionBox = ActionBox(self)

        Layout = QVBoxLayout()
        Layout.addWidget(self.criteriaBox)
        Layout.addWidget(self.hr1)
        Layout.addWidget(self.actionBox)
        Layout.addStretch(10)
        self.setLayout(Layout)

        self.image = QImage(":/box-bg-1.jpg")
        self.emptyImage = QImage(":/no-bindings-yet.png")

        # init

        self.clear()

    def paintEvent(self, e):
        e.accept()
        p = QPainter(self)
        p.setBrush(QBrush(self.image))
        p.setPen(Qt.transparent)
        p.drawRect(self.rect())
        if not self.binding:
            rect = QRect(self.width() / 2 - self.emptyImage.width() / 2,
                         40,
#                         self.height() / 2 - self.emptyImage.height() / 2,
                         self.emptyImage.width(), self.emptyImage.height())
            p.drawImage(rect, self.emptyImage, self.emptyImage.rect())
        
    def init(self, binding):
        self.criteriaBox.init(binding)
        self.actionBox.init(binding)
        self.criteriaBox.show()
        self.actionBox.show()
        self.binding = binding

    def clear(self):
        self.criteriaBox.hide()
        self.criteriaBox.clear()
        self.actionBox.hide()
        self.actionBox.clear()
        self.binding = None

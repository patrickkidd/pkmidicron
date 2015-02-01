from .pyqt_shim import *
from . import util, midiedit
import rtmidi


class CriteriaBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, QPixmap(':/Criteria.png'), parent)

        self.midiEdit = midiedit.MidiEdit(self.content, portBox=True, any=True)

        Layout = QHBoxLayout()
        Layout.addWidget(self.midiEdit)
        Layout.addSpacing(1)
        Layout.setContentsMargins(-1, 0, -1, -1) # just remove top margin
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

    BUTTON_WIDTH = 75
    SPACING = 10

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
        LabelLayout = QHBoxLayout()
        LabelLayout.addWidget(self.titleLabel)
        LabelLayout.addStretch(1)
        LabelLayout.addWidget(self.removeButton)
        LabelLayout.setContentsMargins(0, 0, 0, 0)
        MainLayout = QVBoxLayout() # obtained by subclasses via layout()
        MainLayout.addLayout(LabelLayout)
        MainLayout.addSpacing(1)
        MainLayout.setSpacing(0)
        self.setLayout(MainLayout)

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

        self.forwardBox = QCheckBox('Forward Triggering Message', self)
        self.forwardBox.setChecked(action.forward)
        self.forwardBox.toggled.connect(self.setForward)
        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(action.testScript)
        self.testButton.setFixedWidth(self.BUTTON_WIDTH)

        Layout1 = QHBoxLayout()
        Layout1.addWidget(self.midiEdit)
        Layout1.setContentsMargins(0, 0, 0, 0)
        Layout1.setSpacing(0)
        Layout2 = QHBoxLayout()
        Layout2.addWidget(self.forwardBox)
        Layout2.addSpacing(10)
        Layout2.addWidget(self.testButton)
        Layout2.setContentsMargins(0, 0, 0, 0)
        self.layout().addLayout(Layout1)
        self.layout().addLayout(Layout2)

    def init(self, action):
        super().init(action)
        self.midiEdit.init(action.midiMessage)
        self.setForward(action.forward, False)

    def setForward(self, on, save=True):
        if save:
            self.action.setForward(on)
        for w in self.midiEdit.findChildren(QComboBox):
            if w != self.midiEdit.portBox:
                w.setEnabled(not on)


class RunProgramAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Run Program"), parent)

        self.cmdEdit = QLineEdit(self)
        self.cmdEdit.textChanged.connect(self.setCmd)
        self.selectButton = QPushButton('...', self)
        self.selectButton.clicked.connect(self.onSelectButton)
        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(action.testScript)
        self.testButton.setFixedWidth(self.BUTTON_WIDTH)
        Layout = QHBoxLayout()
        Layout.addWidget(self.cmdEdit)
        Layout.addWidget(self.selectButton)
        Layout.addWidget(self.testButton)
        Layout.setSpacing(self.SPACING)
        self.layout().addLayout(Layout)

    def init(self, action):
        super().init(action)
        self.block = True
        self.cmdEdit.setText(action.text)
        self.block = False

    def setCmd(self, x):
        if self.block: return
        self.action.setText(x)

    def onSelectButton(self):
        path = QFileDialog.getOpenFileName()[0]
        if path:
            self.cmdEdit.setText(path)


class OpenFileAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Open File"), parent)

        self.cmdEdit = QLineEdit(self)
        self.cmdEdit.textChanged.connect(self.setCmd)
        self.selectButton = QPushButton('...', self)
        self.selectButton.clicked.connect(self.onSelectButton)
        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(action.testScript)
        self.testButton.setFixedWidth(self.BUTTON_WIDTH)
        Layout = QHBoxLayout()
        Layout.addWidget(self.cmdEdit)
        Layout.addWidget(self.selectButton)
        Layout.addWidget(self.testButton)
        Layout.setSpacing(self.SPACING)
        self.layout().addLayout(Layout)

    def init(self, action):
        super().init(action)
        self.cmdEdit.setText(action.text)

    def setCmd(self, x):
        self.action.text = x

    def onSelectButton(self):
        path = QFileDialog.getOpenFileName()[0]
        if path:
            self.cmdEdit.setText(path)


class RunScriptAction(ActionWidget):
    def __init__(self, action, parent=None):
        ActionWidget.__init__(self, action, tr("Run Script"), parent)

        self.nameLabel = QLabel(tr('Name:'), self)
        self.nameEdit = QLineEdit(self)
        self.nameEdit.setText(action.name)
        self.nameEdit.textChanged.connect(self.setName)

        self.editButton = QPushButton(tr('...'), self)
        self.editButton.clicked.connect(action.showEditor)

        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(action.testScript)
        self.testButton.setFixedWidth(self.BUTTON_WIDTH)

#        self.editButton.setFixedWidth(100)

        Layout = QHBoxLayout()
        Layout.addWidget(self.nameLabel)
        Layout.addWidget(self.nameEdit)
        Layout.addWidget(self.editButton)
        Layout.addWidget(self.testButton)
        Layout.setSpacing(self.SPACING)
        self.layout().addLayout(Layout)

    def setName(self, x):
        self.action.setName(x)


class ActionBox(util.CollapsableBox):
    def __init__(self, parent=None):
        util.CollapsableBox.__init__(self, QPixmap(':/Actions.png'), parent)

        self.widgets = []
        self.block = False

        self.addBox = QComboBox(self)
        self.addBox.addItem('Send message')
        self.addBox.addItem('Run Program')
        self.addBox.addItem('Open File')
        self.addBox.addItem('Run Script')
        self.addBox.setCurrentIndex(-1)
        self.addBox.activated.connect(self.addAction)
        self.addBox.installEventFilter(self)
        self.header.layout().insertWidget(2, self.addBox)

        self.actionsLayout = QVBoxLayout()
        Layout = QVBoxLayout()
        Layout.addLayout(self.actionsLayout)
        Layout.setContentsMargins(-1, 0, -1, -1) # remove top margin
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
        if self.block:
            return
        self.block = True
        self.addBox.setCurrentIndex(-1)
        self.block = False
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

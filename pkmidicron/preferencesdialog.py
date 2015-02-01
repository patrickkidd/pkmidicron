import sys
from .pyqt_shim import *
from . import util, preferencesdialog_form
from .ports import inputs


class PortListWidget(QWidget):

    def __init__(self, item, **kwargs):
        super().__init__()
        self.item = item
        self.isVirtual = kwargs['isVirtual']

        self.enabledBox = QCheckBox(self)
        self.enabledBox.setChecked(kwargs['enabled'])

        self.nameEdit = util.ClickToEdit(self)
        self.nameEdit.setText(kwargs['portName'])
        self.nameEdit.setReadOnly(True)
        self.nameEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        self.removeButton = QPushButton(self)
        self.removeButton.setIcon(QIcon(QPixmap(":/icons/retina/multiply.png")))
        self.removeButton.hide()

        Layout = QHBoxLayout()
        Layout.addWidget(self.enabledBox)
        Layout.addWidget(self.nameEdit, 10)
        self.setLayout(Layout)
        m = Layout.contentsMargins()
        Layout.setContentsMargins(m.left(), 0, m.right(), 0)

        if self.isVirtual:
            self.removeButton.show()
            Layout.addStretch(1)
            Layout.addWidget(self.removeButton)
        else:
            self.nameEdit.setDisableClick(True)
            self.removeButton.hide()

    def paintEvent(self, e):
        if self.item.isVirtual:
            p = QPainter(self)
            p.setPen(Qt.transparent)
            gradient = QLinearGradient(QPointF(0, 0), QPointF(self.rect().width(), 0))
            gradient.setColorAt(0., Qt.transparent)
            gradient.setColorAt(1., QColor(255, 200, 200, 40))
            p.setBrush(gradient)
            p.drawRect(self.rect())


class PortListItem(QListWidgetItem):
    def __init__(self, listWidget, prefsDialog, **kwargs):
        super().__init__() # set list widget later
        self.setSizeHint(QSize(10, 35))
        self.isVirtual = kwargs['isVirtual']
        self.name = kwargs['portName']
        self.prefsDialog = prefsDialog

        self.widget = PortListWidget(self, **kwargs)

        self.widget.enabledBox.toggled.connect(self.setEnabled)
        self.widget.removeButton.clicked.connect(self.removeMe)
        self.widget.nameEdit.editingFinished.connect(self.onNameChanged)

    def added(self):
        self.listWidget().setItemWidget(self, self.widget)

    def setEnabled(self, x):
        self.prefsDialog.setPortEnabled(self.name, x)

    def onNameChanged(self):
        newName = self.widget.nameEdit.text()
        self.prefsDialog.renamePort(self.name, newName)
        self.name = newName

    def removeMe(self):
        self.prefsDialog.removeThisPort(self)


class PreferencesDialog(QDialog):
    def __init__(self, mainwindow):
        QDialog.__init__(self, mainwindow)
        self.ui = preferencesdialog_form.Ui_PreferencesDialog()
        self.ui.setupUi(self)
        self.mainwindow = mainwindow

        x = self.mainwindow.toolbar.toolButtonStyle()
        self.ui.iconOnlyButton.setChecked(x == Qt.ToolButtonIconOnly)
        self.ui.iconPlusNameButton.setChecked(x == Qt.ToolButtonTextUnderIcon)

        self.ui.iconOnlyButton.toggled.connect(self.setIconOnly)
        self.ui.iconPlusNameButton.toggled.connect(self.setIconPlusName)
        self.ui.portList.installEventFilter(self)
        self.ui.addPortButton.clicked.connect(self.addPort)
        self.ui.addPathButton.clicked.connect(self.addPythonPath)

        self.ui.enableAllInputsBox.setChecked(self.mainwindow.enableAllInputs)
        self.ui.enableAllInputsBox.toggled.connect(self.setEnableAllInputs)
        self.ui.portList.setEnabled(not self.mainwindow.enableAllInputs)

        self.installEventFilter(self)

        for name in inputs().names():
            self.onInputPortAdded(name)
        inputs().portAdded.connect(self.onInputPortAdded)
        inputs().portRemoved.connect(self.onInputPortRemoved)

        self.prefs().beginGroup('python/paths')
        for i in self.prefs().childGroups():
            path = self.prefs().value('paths/' + i, type=str)
            if not path in sys.path:
                sys.path.append(path)
        for path in sys.path:
            item = QListWidgetItem(path, self.ui.pythonPathList)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.ui.pythonPathList.itemChanged.connect(self.onPythonPathChanged)
        self.prefs().endGroup()

    def prefs(self):
        return self.mainwindow.prefs

    def setIconOnly(self, x):
        if x:
            self.mainwindow.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

    def setIconPlusName(self, x):
        if x:
            self.mainwindow.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

    def addPort(self):
        found = False
        i = 1
        while not found:
            name = 'Virtual Port %i' % i
            if not name in inputs().names:
                found = True
            i += 1
        inputs().addVirtualPort(name)
        self.setPortEnabled(name, True)

    def onInputPortAdded(self, name):
        isVirtual = name in inputs().virtualPorts
        enabled = self.prefs().value('InputPorts/%s/enabled' % name, type=bool, defaultValue=True)
        item = PortListItem(self.ui.portList, self, portName=name, isVirtual=isVirtual, enabled=enabled)
        iPort = inputs().names().index(name)
        self.ui.portList.insertItem(iPort, item)
        item.added()
        item.widget.enabledBox.setChecked(enabled)

    def eventFilter(self, o, e):
        if e.type() == QEvent.KeyPress:
            # this was clicking the add button for some reason. WTF?!
            if e.key() in [Qt.Key_Return, Qt.Key_Enter]:
                return True
        return super().eventFilter(o, e)

    def removeThisPort(self, item):
        if not item.isVirtual:
            return
        name = item.name
        inputs().removeVirtualPort(name)
        self.prefs().remove('InputPorts/' + name)

    def onInputPortRemoved(self, name):
        for i in range(self.ui.portList.count()):
            item = self.ui.portList.item(i)
            if item.name == name:
                self.ui.portList.takeItem(i)
                return

    def setEnableAllInputs(self, on):
        self.prefs().setValue('EnableAllInputs', bool(on))
        self.ui.portList.setEnabled(not on)
        self.mainwindow.setEnableAllInputs(on)

    def setPortEnabled(self, name, x):
        self.prefs().setValue('InputPorts/%s/enabled' % name, bool(x))
        if not self.mainwindow.enableAllInputs:
            self.mainwindow.setInputPortEnabled(name, x)

    def renamePort(self, oldName, newName):
        self.prefs().beginGroup('InputPorts/%s' % oldName)
        enabled = self.prefs().value('enabled', type=bool)
        self.prefs().endGroup()
        inputs().renameVirtualPort(oldName, newName)
        self.prefs().remove('InputPorts/%s' % oldName)
        self.prefs().beginGroup('InputPorts/%s' % newName)
        self.prefs().setValue('enabled', enabled)
        self.prefs().endGroup()

    def addPythonPath(self):
        item = QListWidgetItem('something', self.ui.pythonPathList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)

    def onPythonPathChanged(self, item):
        print(item.text())

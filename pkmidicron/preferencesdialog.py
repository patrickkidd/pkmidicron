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
        self.block = False

        #self.actionDeleteBinding.setShortcut(_translate("MainWindow", "Backspace"))

        self.ui.enableNetworkingBox.setChecked(self.mainwindow.enableNetworking)
        self.ui.enableNetworkingBox.toggled.connect(self.mainwindow.setEnableNetworking)

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

        self.ui.pythonPathList.installEventFilter(self)
        self.installEventFilter(self)

        for name in inputs().names():
            self.onInputPortAdded(name)
        inputs().portAdded.connect(self.onInputPortAdded)
        inputs().portRemoved.connect(self.onInputPortRemoved)

        self.originalPaths = list(sys.path)
        self.prefs().beginGroup('Python/Paths')
        for i in self.prefs().childKeys():
            path = self.prefs().value(i, type=str)
            sys.path.append(path)
            item = QListWidgetItem(path, self.ui.pythonPathList)
            item.setFlags(item.flags() | Qt.ItemIsEditable)
        self.ui.pythonPathList.itemChanged.connect(self.onPythonPathChanged)
        self.prefs().endGroup()

    def event(self, e):
        """ no idea why this has to go here """
        if e.type() == QEvent.KeyPress and e.key() == Qt.Key_Backspace:
            if QApplication.focusWidget() == self.ui.pythonPathList:
                e.accept()
                self.removeSelectedPythonPath()
                return True
        return super().event(e)

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
            if not name in inputs().names():
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
        if o == self.ui.pythonPathList:
            if e.type() == QEvent.DragEnter:
                e.accept()
                return True
            elif e.type() == QEvent.Drop:
                for url in e.mimeData().urls():
                    if url.isLocalFile():
                        fpath = url.toLocalFile()
                        if QFileInfo(fpath).isDir() or fpath.endswith('.zip'):
                            self.addPythonPath(url.toLocalFile())
                e.accept()
                return True
        elif e.type() == QEvent.KeyPress:
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

    def addPythonPath(self, path=QDir.homePath()):
        if type(path) == bool: # default argument
            path = QDir.homePath()
        self.block = True
        item = QListWidgetItem(path, self.ui.pythonPathList)
        item.setFlags(item.flags() | Qt.ItemIsEditable)
        if QFileInfo(path).isDir() or path.endswith('.zip'):
            item.setText(path)
        self.block = False
        self.savePythonPaths()

    def onPythonPathChanged(self, item):
        if self.block:
            return
        self.savePythonPaths()

    def removeSelectedPythonPath(self):
        items = self.ui.pythonPathList.selectedItems()
        if not items:
            return
        item = items[0]
        sys.path.remove(item.text())
        self.ui.pythonPathList.takeItem(self.ui.pythonPathList.row(item))
        self.savePythonPaths()

    def savePythonPaths(self):
        if self.block:
            return
        self.block = True
        sys.path = self.originalPaths
        self.prefs().beginGroup('Python/Paths')
        self.prefs().remove('')
        index = 0
        for item in self.ui.pythonPathList.findItems('*', Qt.MatchWildcard):
            self.prefs().setValue(str(index), item.text())
            item.setData(Qt.UserRole, index)
            sys.path.append(item.text())
            index += 1
        self.prefs().endGroup()
        self.prefs().sync()
        self.block = False

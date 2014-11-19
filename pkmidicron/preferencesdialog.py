from .pyqt_shim import *
from . import util, preferencesdialog_form
from .ports import ports


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

        self.installEventFilter(self)

        for name in ports().allPorts():
            self.onPortAdded(name)
        ports().portAdded.connect(self.onPortAdded)
        ports().portRemoved.connect(self.onPortRemoved)

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
            if not name in ports().names:
                found = True
            i += 1
        ports().addVirtualPort(name)
        self.setPortEnabled(name, True)

    def onPortAdded(self, name):
        isVirtual = name in ports().virtualPorts
        enabled = self.prefs().value('InputPorts/%s/enabled' % name, type=bool)
        item = PortListItem(self.ui.portList, self, portName=name, isVirtual=isVirtual, enabled=enabled)
        iPort = ports().allPorts().index(name)
        self.ui.portList.insertItem(iPort, item)
        self.item.added()
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
        ports().removeVirtualPort(name)
        self.prefs().remove('InputPorts/' + name)

    def onPortRemoved(self, name):
        for i in range(self.ui.portList.count()):
            item = self.ui.portList.item(i)
            if item.name == name:
                self.ui.portList.takeItem(i)
                return

    def setPortEnabled(self, name, x):
        self.prefs().setValue('InputPorts/%s/enabled' % name, bool(x))
        self.mainwindow.setInputPortEnabled(name, x)

    def renamePort(self, oldName, newName):
        self.prefs().beginGroup('InputPorts/%s' % oldName)
        enabled = self.prefs().value('enabled', type=bool)
        self.prefs().endGroup()
        ports().renameVirtualPort(oldName, newName)
        self.prefs().remove('InputPorts/%s' % oldName)
        self.prefs().beginGroup('InputPorts/%s' % newName)
        self.prefs().setValue('enabled', enabled)
        self.prefs().endGroup()

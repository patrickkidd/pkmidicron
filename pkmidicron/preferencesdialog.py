from .pyqt_shim import *
from . import util, preferencesdialog_form
from .ports import ports


class PortListWidget(QWidget):

    def __init__(self, item):
        super().__init__()
        self.item = item
        self.label = QLabel("virtual", self)
        self.label.hide()
        font = self.label.font()
        font.setPixelSize(8)
        self.label.setFont(font)
        p = QPalette(self.label.palette())
        p.setColor(QPalette.Text, Qt.gray)

    def resizeEvent(self, e):
        if self.item.isVirtual:
#            self.label.show()
            self.label.resize(self.label.sizeHint())
            self.label.move(self.width() - self.label.width() - 5, 5)
        else:
            self.label.hide()
        self.item.resizeEvent(e)

    def paintEvent(self, e):
        if self.item.isVirtual and not self.item.isSelected():
            p = QPainter(self)
            p.setPen(Qt.transparent)
            p.setBrush(QColor(255, 200, 200, 40))
            p.drawRect(self.rect())


class PortListItem(QListWidgetItem):
    def __init__(self, portName, listWidget, prefsDialog):
        super().__init__(listWidget)
        self.setSizeHint(QSize(10, 40))
        self.isVirtual = False
        self.name = portName
        self.prefsDialog = prefsDialog

        widget = self._widget = PortListWidget(self)
        self.listWidget().setItemWidget(self, widget)
        self.enabledBox = QCheckBox(widget)
        self.enabledBox.toggled.connect(self.setEnabled)

        self.nameEdit = util.ClickToEdit(widget)
        self.nameEdit.setText(portName)
        self.nameEdit.setReadOnly(True)
        self.nameEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.nameEdit.clicked.connect(self.onNameClicked)
        self.nameEdit.editingFinished.connect(self.onNameChanged)

        self.removeButton = QPushButton(widget)
        self.removeButton.setIcon(QIcon(QPixmap(":/icons/retina/multiply.png")))
        self.removeButton.clicked.connect(self.removeMe)
        self.removeButton.hide()

        Layout = QHBoxLayout()
        m = Layout.contentsMargins()
        Layout.setContentsMargins(m.left(), 0, m.right(), 0)
        Layout.addWidget(self.enabledBox)
        Layout.addWidget(self.nameEdit)
        Layout.addStretch(2)
        Layout.addWidget(self.removeButton)
        widget.setLayout(Layout)

    def resizeEvent(self, e):
        if self.isVirtual:
            self.removeButton.show()

    def setEnabled(self, x):
        self.prefsDialog.setPortEnabled(self.name, x)

    def onNameClicked(self):
        self.setSelected(True)
        self.listWidget().setCurrentItem(self)
    
    def onNameChanged(self):
        newName = self.nameEdit.text()
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

    def onPortAdded(self, name):
        item = PortListItem(name, self.ui.portList, self)
        enabled = self.prefs().value('InputPorts/%s/enabled' % name, type=bool)
        item.enabledBox.setChecked(enabled)
        if name in ports().virtualPorts:
            item.isVirtual = True

    def eventFilter(self, o, e):
        if o == self.ui.portList and e.type() == QEvent.KeyPress:
            if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
                self.removeSelectedPort()
                return True
        return super().eventFilter(o, e)

    def removeSelectedPort(self):
        items = self.ui.portList.selectedItems()
        if not items or not items[0].isVirtual:
            return
        self.removeThisPort(items[0])

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

    def renamePort(self, oldName, newName):
        self.prefs().beginGroup('InputPorts/%s' % oldName)
        enabled = self.prefs().value('enabled', type=bool)
        self.prefs().endGroup()
        ports().renameVirtualPort(oldName, newName)
        self.prefs().remove('InputPorts/%s' % oldName)
        self.prefs().beginGroup('InputPorts/%s' % newName)
        self.prefs().setValue('enabled', enabled)
        self.prefs().endGroup()

from .pyqt_shim import *
from . import util
from rtmidi import *


class Proxy(QObject):
    changed = pyqtSignal()


class ClickToEdit(QLineEdit):

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)

    def mouseDoubleClickEvent(self, e):
        if self.isReadOnly():
            self.setReadOnly(False)
            self.setFocus(Qt.MouseFocusReason)
            self.selectAll()

    def focusOutEvent(self, e):
        self.setReadOnly(True)

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.setReadOnly(True)


class Widget(util.Led):
    def __init__(self, item):
        super().__init__()
        self.item = item

    def resizeEvent(self, e):
        self.item.resizeEvent(e)

class BindingListItem(QListWidgetItem):
    def __init__(self, parent, binding):
        QListWidgetItem.__init__(self, parent)
        self.binding = binding
        self.proxy = Proxy()
        self.changed = self.proxy.changed

        self.widget = Widget(self)
        self.widget.setColor(Qt.red)
        self.enabledBox = QCheckBox(self.widget)
        self.nameEdit = ClickToEdit(self.widget)
        self.nameEdit.move(30, 0)
        self.nameEdit.setReadOnly(True)
        self.nameEdit.setText(binding.title)
        self.nameEdit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.nameEdit.clicked.connect(self.onNameClicked)
        self.nameEdit.textChanged.connect(self.onNameChanged)
        self.countLabel = QLabel('triggered 0 times', self.widget)
        font = self.countLabel.font()
        font.setPixelSize(8)
        self.countLabel.setFont(font)
        p = QPalette(self.countLabel.palette())
        p.setColor(QPalette.Text, Qt.gray)
        self.countLabel.setPalette(p)
        self.countLabel.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.setSizeHint(QSize(100, 40))
        parent.setItemWidget(self, self.widget)

        self.binding.triggered.connect(self.onTriggered)

        Layout = QHBoxLayout()
        Layout.addWidget(self.enabledBox)
        Layout.addWidget(self.nameEdit)
        Layout.addStretch(1)
        self.widget.setLayout(Layout)

        self.resizeEvent(None)

    def updateTriggerCount(self):
        self.countLabel.setText('triggered %i times' % self.binding.triggerCount)
        self.countLabel.resize(self.countLabel.sizeHint())
        self.countLabel.move(self.widget.width() - 5 - self.countLabel.width(),
                             self.widget.height() - 2 - self.countLabel.height())

    def resizeEvent(self, e):
        self.updateTriggerCount()

    def onNameClicked(self):
        self.setSelected(True)
    
    def onNameChanged(self, x):
        self.binding.setTitle(x)

    def onTriggered(self):
        self.updateTriggerCount()
        self.widget.flash()
        

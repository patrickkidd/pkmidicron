from .pyqt_shim import *
from . import util
from rtmidi import *
import time
#from PyQt5 import QtCore, QtGui


class Proxy(QObject):
    changed = pyqtSignal()


class ClickToEdit(QLineEdit):

    clicked = pyqtSignal()

    def __init__(self, parent=None):
        QLineEdit.__init__(self, parent)
        self.clickTimer = QTimer(parent)
        self.clickTimer.timeout.connect(self.clickTimerTimeout)
        self.lastRelease = 0

        self.textAnimation = QPropertyAnimation(self, "textColor", self)
        self.textAnimation.setDuration(500)
        self.textAnimation.setStartValue(QColor("red"))
        self.textAnimation.setEndValue(self.palette().color(QPalette.Text))
        self.textAnimation.setEasingCurve(QEasingCurve.InOutQuad)

    def clickTimerTimeout(self):
        self.clicked.emit()
        self.clickTimer.stop()

    def mouseReleaseEvent(self, e):
        x = time.time()
        if x - self.lastRelease > .1: # single double click
            self.clickTimer.stop()
            self.clickTimer.start(110)
            e.accept()
        self.lastRelease = x

    def mouseDoubleClickEvent(self, e):
        self.clickTimer.stop()
        if self.isReadOnly():
            self.setReadOnly(False)
            self.setFocus(Qt.MouseFocusReason)
            self.selectAll()

    def focusOutEvent(self, e):
        self.setReadOnly(True)
        self.deselect()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.setReadOnly(True)

    @pyqtProperty(QColor)
    def textColor(self):
        return self.palette().text().color()

    @textColor.setter
    def textColor(self, x):
        if x.__class__ == QBrush:
            x = x.color()
        p = self.palette()
        p.setColor(QPalette.Text, x)
        self.setPalette(p)
        
    def flash(self):
        self.textAnimation.stop()
        self.textAnimation.start()


class Widget(util.Led):
    def __init__(self, item):
        super().__init__()
        self.item = item

    def resizeEvent(self, e):
        self.item.resizeEvent(e)


class BindingListItem(QListWidgetItem):
    def __init__(self, parent, binding):
        QListWidgetItem.__init__(self, parent)
        self.setSizeHint(QSize(100, 40))

        self.binding = binding
        self.binding.triggered.connect(self.onTriggered)

        self.proxy = Proxy()
        self.changed = self.proxy.changed

        self.widget = Widget(self)
        self.widget.setColor(Qt.red)
        parent.setItemWidget(self, self.widget)

        self.enabledBox = QCheckBox(self.widget)
        self.enabledBox.setChecked(binding.enabled)
        self.enabledBox.stateChanged.connect(self.setEnabled)

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

        Layout = QHBoxLayout()
        Layout.addWidget(self.enabledBox)
        Layout.addWidget(self.nameEdit)
        Layout.addStretch(1)
        self.widget.setLayout(Layout)

        self.resizeEvent(None)

    def updateTriggerCount(self):
        if not hasattr(self, 'countLabel'):
            return
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
        self.nameEdit.flash()

    def setEnabled(self, state):
        self.binding.setEnabled(state == Qt.Checked)


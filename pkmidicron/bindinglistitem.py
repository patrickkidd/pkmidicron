from .pyqt_shim import *
from . import util
import time


class Proxy(QObject):
    changed = pyqtSignal()



class Widget(QWidget):
    def __init__(self, item):
        super().__init__()
        self.item = item

    def resizeEvent(self, e):
        self.item.resizeEvent(e)


class BindingListItem(QListWidgetItem):
    def __init__(self, parent, binding):
        QListWidgetItem.__init__(self, parent)
        self.setSizeHint(QSize(100, 45))

        self.binding = binding
        self.binding.triggered.connect(self.onTriggered)

        self.proxy = Proxy()
        self.changed = self.proxy.changed

        self.widget = Widget(self)
        parent.setItemWidget(self, self.widget)

        self.enabledBox = QCheckBox(self.widget)
        self.enabledBox.setChecked(binding.enabled)
        self.enabledBox.stateChanged.connect(self.setEnabled)

        self.nameEdit = util.ClickToEdit(self.widget)
        self.nameEdit.move(30, 0)
        self.nameEdit.setReadOnly(True)
        self.nameEdit.setText(binding.title)
        self.nameEdit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
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
        self.listWidget().setCurrentItem(self)
    
    def onNameChanged(self, x):
        self.binding.setTitle(x)

    def onTriggered(self):
        self.updateTriggerCount()
        self.nameEdit.flash()

    def setEnabled(self, state):
        self.binding.setEnabled(state == Qt.Checked)


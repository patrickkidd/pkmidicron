from .pyqt_shim import Qt, QListWidget, pyqtSignal
from .bindinglistitem import BindingListItem


class BindingListWidget(QListWidget):

    deleted = pyqtSignal(BindingListItem)

    def __init__(self, parent=None):
        QListWidget.__init__(self, parent)

    def _keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Delete or e.key() == Qt.Key_Backspace:
            if self.currentRow() != -1:
                item = self.takeItem(self.currentRow())
                self.deleted.emit(item)
                e.accept()
                return
        e.ignore()

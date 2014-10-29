from .pyqt_shim import *
from . import util, preferencesdialog_form

class PreferencesDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)
        self.ui = preferencesdialog_form.Ui_PreferencesDialog()
        self.ui.setupUi(self)

        x = util.mainwindow.toolbar.toolButtonStyle()
        self.ui.iconOnlyButton.setChecked(x == Qt.ToolButtonIconOnly)
        self.ui.iconPlusNameButton.setChecked(x == Qt.ToolButtonTextUnderIcon)

        self.ui.iconOnlyButton.toggled.connect(self.setIconOnly)
        self.ui.iconPlusNameButton.toggled.connect(self.setIconPlusName)

    def setIconOnly(self, x):
        if x:
            util.mainwindow.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)

    def setIconPlusName(self, x):
        if x:
            util.mainwindow.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

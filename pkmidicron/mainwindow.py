import rtmidi
from .pyqt_shim import *
from . import util, mainwindow_form, bindinglistitem, patch


FILE_TYPES = "PKMidiCron files (*.pmc)"
CONFIRM_SAVE = False




class MainWindow(QMainWindow):
    def __init__(self, prefs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = mainwindow_form.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setMinimumWidth(875)
        self.resize(600, 200)

        self.collector = util.CollectorBin(self)
        self.collector.message.connect(self.onMidiMessage)
        self.collector.start()

        self.ui.simulatorTabs.setTabBar(util.EmptyTabBar())

        self.toolbar = self.addToolBar(tr("File"))
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(40, 40))
#        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.newAction = self.toolbar.addAction(tr("New"))
        self.newAction.setIcon(QIcon(':/icons/retina/doc 5.png'))
        self.newAction.triggered.connect(self.new)
        self.openAction = self.toolbar.addAction(tr("Open"))
        self.openAction.setIcon(QIcon(':/icons/retina/folder.png'))
        self.openAction.triggered.connect(self.open)
        self.saveAction = self.toolbar.addAction(tr('Save'))
        self.saveAction.setIcon(QIcon(':/icons/retina/floppy disk.png'))
        self.saveAction.triggered.connect(self.save)
        self.saveAction.setEnabled(False)
        spacer = QWidget(self.toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        self.addAction = self.toolbar.addAction(tr('&Add'))
        self.addAction.setIcon(QIcon(':/icons/retina/plus.png'))
        self.addAction.triggered.connect(self.addBinding)
        self.deleteAction = self.toolbar.addAction(tr('Delete'))
        self.deleteAction.setIcon(QIcon(':/icons/retina/multiply.png'))
        self.deleteAction.triggered.connect(self.removeSelectedBinding)
        spacer = QWidget(self.toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        spacer = QWidget(self.toolbar)
        spacer.setFixedWidth(77)
        self.toolbar.addWidget(spacer)
        self.removeAction = self.toolbar.addAction(tr('Clear'))
        self.removeAction.setIcon(QIcon(':/icons/retina/dustbin.png'))
        self.removeAction.triggered.connect(self.clearActivityLog)
        
        # Signals
        
        self.activityCount = 0
        self.ui.simulator.received.connect(self.onMidiMessage)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.saveAs)
        self.ui.bindingsList.selectionModel().selectionChanged.connect(self.onBindingSelectionChanged)
        self.ui.bindingsList.deleted.connect(self.onBindingItemRemoved)

        # Init

        self.patch = None
        self.prefs = prefs and prefs or QSettings()
        self.readPrefs()

    # Patch mgmt

    def confirmSave(self):
        if not CONFIRM_SAVE:
            return True
        if self.patch.dirty:
            ret = QMessageBox.question(self, "Save changes?",
                                       "Do you want to save your changes?",
                                       QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                                       QMessageBox.Yes)
            if ret == QMessageBox.Yes:
                self.save()
                return True
            elif ret == QMessageBox.Cancel:
                return False
        return True

    def closeEvent(self, e):
        if not self.confirmSave():
            e.ignore()
            return
        e.accept()
        self.writePrefs()
        self.collector.stop()

    def onDirtyChanged(self, on):
        if on:
            title = self.windowTitle()
            if not title.endswith('*'):
                title = title + ' *'
                self.setWindowTitle(title)
        else:
            title = self.windowTitle()
            if title.endswith(' *'):
                title = title[:-2]
                self.setWindowTitle(title)
        self.saveAction.setEnabled(on)

    def clear(self):
        self._setPatch(patch.Patch())

    def _setPatch(self, patch):
        if self.patch:
            if not self.confirmSave():
                return
            self.patch.setParent(None)
            self.ui.bindingsList.clear()
            self.ui.simulator.clear()
        self.patch = patch
        self.patch.setParent(self)
        for binding in self.patch.bindings:
            self.addBinding(binding)
        self.ui.simulator.init(patch.simulator)
        self.patch.setDirty(False)
        self.patch.dirtyChanged.connect(self.onDirtyChanged)

    def new(self):
        if not self.confirmSave():
            return
        self.clear()
        self.prefs.setValue('lastFilePath', '')
        self.setWindowFilePath('')
        self.setWindowTitle('Untitled.pmc')
        self.patch.setDirty(True)

    def save(self, filePath=None):
        if not filePath:
            filePath = self.prefs.value('lastFilePath', type=str)
        if not filePath:
            self.saveAs()
        self.patch.write(filePath)
        self.patch.setDirty(False)
        self.setWindowFilePath(filePath)
        self.setWindowTitle(QFileInfo(filePath).fileName())
        self.prefs.setValue('lastFilePath', filePath)

    def saveAs(self):
        filePath, types = QFileDialog.getSaveFileName(self, "Save File",
                                                      "",
                                                      FILE_TYPES)
        if not filePath:
            return
        self.save(filePath)

    def open(self, filePath=None):
        if not filePath:
            filePath, types = QFileDialog.getOpenFileName(self, "Open File",
                                                          "",
                                                          FILE_TYPES)
        if not filePath:
            return
        p = patch.Patch(self)
        p.read(filePath)
        self._setPatch(p)
        self.setWindowFilePath(filePath)
        self.setWindowTitle(QFileInfo(filePath).fileName())
        self.prefs.setValue('lastFilePath', filePath)

    # General app stuff

    def readPrefs(self):
        self.resize(self.prefs.value('size', type=QSize))
        state = self.prefs.value('outerSplitter')
        if state:
            self.ui.outerSplitter.setSizes(state)
        state = self.prefs.value('innerSplitter')
        if state:
            self.ui.innerSplitter.setSizes(state)
        filePath = self.prefs.value('lastFilePath')
        if filePath:
            self.open(filePath)
        else:
            self._setPatch(patch.Patch())

    def writePrefs(self):
        self.prefs.setValue('size', self.size())
        self.prefs.setValue('outerSplitter', self.ui.outerSplitter.sizes())
        self.prefs.setValue('innerSplitter', self.ui.innerSplitter.sizes())

    def showAbout(self):
        dialog = AboutDialog(self)
        dialog.setModal(True)
        dialog.show()

    # Functionality

    def addBinding(self, binding=None):
        if binding is None or type(binding) == bool:
            binding = self.patch.addBinding()
        bindinglistitem.BindingListItem(self.ui.bindingsList, binding)
        return binding
        
    def removeSelectedBinding(self):
        iItem = self.ui.bindingsList.currentRow()
        item = self.ui.bindingsList.takeItem(iItem)
        self.patch.removeBinding(item.binding)

    def onBindingItemRemoved(self, item):
        self.patch.removeBinding(item.binding)

    def onBindingSelectionChanged(self, x, y):
        if x.indexes():
            self.deleteAction.setEnabled(True)
            item = self.ui.bindingsList.currentItem()
            self.ui.bindingProperties.init(item.binding)
        elif y.indexes():
            self.deleteAction.setEnabled(False)
            self.ui.bindingProperties.clear()

    def clearActivityLog(self):
        self.ui.activityLog.clearContents()
        self.ui.activityLog.setRowCount(0)

    def onMidiMessage(self, portName, midi):
        if self.patch.block:
            return
        s = midi.__str__().replace('<', '').replace('>', '')
        self.activityCount += 1
        items = [
            QTableWidgetItem(str(midi.getTimeStamp())),
            QTableWidgetItem(portName),
            QTableWidgetItem(util.midiTypeString(midi)),
            QTableWidgetItem(str(midi.getChannel())),
            QTableWidgetItem(util.midiDataSummary(midi)),
        ]
        vScrollBar = self.ui.activityLog.verticalScrollBar()
        bottom = vScrollBar.value() == vScrollBar.maximum()
        rows = self.ui.activityLog.rowCount()
        self.ui.activityLog.setRowCount(rows+1)
        for col, item in enumerate(items):
            self.ui.activityLog.setItem(rows, col, items[col])
        if bottom:
            QTimer.singleShot(0, self.ui.activityLog.scrollToBottom)
#        self.ui.activityLog.append('#%i %s: %s' % (self.activityCount, portName, midi))
        self.patch.onMidiMessage(portName, midi)

            


ABOUT_TEXT = """
PKMidiCron %s
<a href="http://vedanamedia.com">vedanamedia.com</a>
"""

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        version = 1.0
        
        self.label = QTextBrowser(self)
        self.label.setHtml(ABOUT_TEXT % version)
#        self.label.setOpenLinks(True)
        self.label.setReadOnly(True)
        Layout = QVBoxLayout()
        Layout.addWidget(self.label)
        self.setLayout(Layout)


import rtmidi
from .pyqt_shim import *
from . import util, binding, mainwindow_form

FILE_TYPES = "PKMidiCron files (*.pmc)"


class MainWindow(QMainWindow):
    def __init__(self, prefs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = mainwindow_form.Ui_MainWindow()
        self.ui.setupUi(self)
        self.setMinimumWidth(875)
        self.resize(600, 200)

        self.dirty = False
        self.bindings = []
        self.prefs = prefs and prefs or QSettings()
        self.patch = QSettings()

        self.collector = util.CollectorBin(self)
        self.collector.message.connect(self.onMidiMessage)
        self.collector.start()

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
        self.addAction = self.toolbar.addAction(tr('&Add'))
        self.addAction.setIcon(QIcon(':/icons/retina/plus.png'))
        self.addAction.triggered.connect(self.addBinding)
        self.deleteAction = self.toolbar.addAction(tr('Delete'))
        self.deleteAction.setIcon(QIcon(':/icons/retina/multiply.png'))
        self.deleteAction.triggered.connect(self.removeSelectedBinding)
        self.saveAction = self.toolbar.addAction(tr('Save'))
        self.saveAction.setIcon(QIcon(':/icons/retina/floppy disk.png'))
        self.saveAction.triggered.connect(self.save)
        spacer = QWidget(self.toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        self.removeAction = self.toolbar.addAction(tr('Clear'))
        self.removeAction.setIcon(QIcon(':/icons/retina/dustbin.png'))
        self.removeAction.triggered.connect(self.clearActivityLog)
        
        # Signals
        
        self.activityCount = 0
        self.ui.simulator.received.connect(self.onMidiMessage)
        self.ui.simulator.changed.connect(self.setDirty)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.saveAs)
        
        # Init

        self.readPrefs()
        lastFilePath = self.prefs.value('lastFilePath', type=str)
        if lastFilePath:
            self.open(lastFilePath)

    def confirmSave(self):
        if self.dirty:
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

    def setDirty(self, x=True):
        if x and self.dirty is False:
            self.dirty = True
            title = self.windowTitle()
            if not title.endswith('*'):
                title = title + ' *'
                self.setWindowTitle(title)
        elif not x and self.dirty is True:
            self.dirty = False
            title = self.windowTitle()
            if title.endswith(' *'):
                title = title[:-2]
                self.setWindowTitle(title)

    def readPrefs(self):
        self.resize(self.prefs.value('size', type=QSize))
        state = self.patch.value('splitter')
        if state:
            self.ui.splitter.setSizes(state)

    def writePrefs(self):
        self.prefs.setValue('size', self.size())
        self.prefs.setValue('splitter', self.ui.splitter.sizes())        

    def readPatch(self, patch):
        i = 0
        patch.beginGroup('bindings')
        keys = patch.childGroups()
        found = True
        while found:
            key = str(i)
            patch.beginGroup(key)
            found = len(patch.allKeys()) > 0
            if found:
                b = self.addBinding(save=False)
                b.readPatch(patch)
            patch.endGroup()
            i += 1
        patch.endGroup()
        patch.beginGroup('simulator')
        self.ui.simulator.readPatch(patch)
        patch.endGroup()

    def writePatch(self, patch):
        self.writeBindingsPatch(patch)
        patch.beginGroup('simulator')
        self.ui.simulator.writePatch(patch)
        patch.endGroup()
        patch.sync()
        
    def writeBindingsPatch(self, patch=None):
        if patch is None:
            patch = self.patch
        patch.remove('bindings')
        patch.beginGroup('bindings')
        for i, b in enumerate(self.bindings):
            patch.beginGroup(str(i))
            b.writePatch(patch)
            patch.endGroup()
        patch.endGroup()

    def onMidiMessage(self, portName, midi):
        s = midi.__str__().replace('<', '').replace('>', '')
        self.activityCount += 1
        self.ui.activityLog.append('#%i %s: %s' % (self.activityCount, portName, midi))
        for b in self.bindings:
            b.match(portName, midi)

    def addBinding(self, save=True):
        b = binding.Binding(self.ui.bindingsWidget)
        self.ui.bindingsLayout.insertWidget(self.ui.bindingsLayout.count()-1, b)
        b.changed.connect(self.bindingChanged)
        self.bindings.append(b)
        self.patch.beginGroup('bindings/%s' % (len(self.bindings) - 1))
        b.writePatch(self.patch)
        self.patch.endGroup()
        b.removeMe.connect(self.removeBinding)
        if save:
            self.patch.sync()
        self.setDirty(True)
        return b
        
    def removeBinding(self, b, save=True):
        self.ui.bindingsLayout.removeWidget(b)
        self.bindings.remove(b)
        b.setParent(None)
        if save:
            self.writeBindingsPatch()
        self.setDirty(True)

    def removeSelectedBinding(self):
        pass

    def bindingChanged(self):
        self.writeBindingsPatch(self.patch)
        self.setDirty(True)

    def showAbout(self):
        dialog = AboutDialog(self)
        dialog.setModal(True)
        dialog.show()

    def new(self):
        if not self.confirmSave():
            return
        for b in list(self.bindings):
            self.removeBinding(b, False)
        self.prefs.setValue('lastFilePath', '')
        self.setWindowFilePath('')
        self.setWindowTitle('Untitled.pmc')
        self.setDirty(False)

    def save(self, filePath=None):
        if not filePath:
            filePath = self.prefs.value('lastFilePath', type=str)
        if not filePath:
            self.saveAs()
            return
        patch = QSettings(filePath, QSettings.NativeFormat)
        self.writePatch(patch)
        self.patch = patch
        self.prefs.setValue('lastFilePath', filePath)
        self.setDirty(False)

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
        patch = QSettings(filePath, QSettings.NativeFormat)
        self.readPatch(patch)
        self.prefs.setValue('lastFilePath', filePath)
        self.setWindowFilePath(filePath)
        self.setWindowTitle(QFileInfo(filePath).fileName())
        self.setDirty(False)

    def clearActivityLog(self):
        self.ui.activityLog.clear()

            


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


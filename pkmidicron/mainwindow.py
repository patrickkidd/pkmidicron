import rtmidi
from .pyqt_shim import *
from . import util, mainwindow_form, bindinglistitem, patch, preferencesdialog_form, preferencesdialog, ports


CONFIRM_SAVE = True


class MainWindow(QMainWindow):
    def __init__(self, prefs, parent=None):
        QMainWindow.__init__(self, parent)
        self.ui = mainwindow_form.Ui_MainWindow()
        self.ui.setupUi(self)

        self.trayIcon = TrayIcon(self)
        self.trayIcon.show()

        self.ui.innerSplitter.setStretchFactor(0, 0)
        self.ui.innerSplitter.setStretchFactor(1, 1)
        self.ui.innerSplitter.setStretchFactor(2, 1)

        self.prefsDialog = None

        self.collector = util.CollectorBin(parent=self, autolist=False)
        self.collector.message.connect(self.onMidiMessage)
        self.collector.start()

        self.toolbar = self.addToolBar(tr("File"))
        self.toolbar.setMovable(False)
        self.toolbar.setIconSize(QSize(40, 40))
        self.toolbar.addAction(self.ui.actionNew)
        self.ui.actionNew.setIcon(QIcon(':/icons/retina/doc 5.png'))
        self.toolbar.addAction(self.ui.actionOpen)
        self.ui.actionOpen.setIcon(QIcon(':/icons/retina/folder.png'))
        self.toolbar.addAction(self.ui.actionSave)
        self.ui.actionSave.setIcon(QIcon(':/icons/retina/floppy disk.png'))
        self.ui.actionSave.setEnabled(False)
        spacer = QWidget(self.toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.ui.actionAddBinding)
        self.ui.actionAddBinding.setIcon(QIcon(':/icons/retina/plus.png'))
        self.toolbar.addAction(self.ui.actionDeleteBinding)
        self.ui.actionDeleteBinding.setIcon(QIcon(':/icons/retina/multiply.png'))
        spacer = QWidget(self.toolbar)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        spacer = QWidget(self.toolbar)
        spacer.setFixedWidth(77)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.ui.actionClearLog)
        self.ui.actionClearLog.setIcon(QIcon(':/icons/retina/dustbin.png'))

        # Signals
        
        self.activityCount = 0
        self.ui.actionPreferences.triggered.connect(self.showPreferences)
        self.ui.simulator.received.connect(self.onMidiMessage)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.ui.actionNew.triggered.connect(self.new)
        self.ui.actionOpen.triggered.connect(self.open)
        self.ui.actionSave.triggered.connect(self.save)
        self.ui.actionSaveAs.triggered.connect(self.saveAs)
        self.ui.actionAddBinding.triggered.connect(self.addBinding)
        self.ui.actionDeleteBinding.triggered.connect(self.removeSelectedBinding)
        self.ui.actionClearLog.triggered.connect(self.clearActivityLog)
        self.ui.bindingsList.selectionModel().selectionChanged.connect(self.onBindingSelectionChanged)
        self.ui.actionExit.triggered.connect(QApplication.quit)
        self.ui.actionToggleSimulator.triggered.connect(self.toggleSimulator)
        self.ui.actionToggleLog.triggered.connect(self.toggleLog)
        self.ui.actionToggleBindingProperties.triggered.connect(self.toggleBindingProperties)
        self.ui.actionToggleMainWindow.triggered.connect(self.toggleMainWindow)

        ports.ports().portAdded.connect(self.collector.addCollector)
        ports.ports().portAdded.connect(self.collector.removeCollector)

        # Init

        self.patch = None
        self.prefs = prefs and prefs or QSettings()
        self.readPrefs()

    # Patch mgmt

    def confirmSave(self):
        if not CONFIRM_SAVE:
            return True
        if self.patch and self.patch.dirty:
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
        self.ui.actionSave.setEnabled(on)

    def clear(self):
        self._setPatch(patch.Patch(), force=True)

    def _setPatch(self, patch, force=False):
        if self.patch:
            if not force and not self.confirmSave():
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
        self.setWindowTitle(self.patch.fileName)

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
        if self.patch.filePath:
            filePath = self.patch.filePath
        elif self.patch.fileName:
            filePath = self.patch.fileName
        else:
            desktopPath = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            filePath = self.prefs.value('lastFileSavePath', type=str,
                                        defaultValue=desktopPath)
        filePath, types = QFileDialog.getSaveFileName(self, "Save File",
                                                      filePath,
                                                      util.FILE_TYPES)
        if not filePath:
            return
        self.prefs.setValue('lastFileSavePath', filePath)
        self.save(filePath)

    def open(self, filePath=None):
        usedDialog = False
        if not filePath:
            desktopPath = QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)
            filePath = self.prefs.value('lastFileOpenPath', type=str,
                                        defaultValue=desktopPath)
            if filePath and QFileInfo(filePath).isFile():
                filePath = QFileInfo(filePath).absolutePath()
            filePath, types = QFileDialog.getOpenFileName(self, "Open File",
                                                          filePath,
                                                          util.FILE_TYPES)
            if filePath:
                usedDialog = True
        if not filePath:
            return
        p = patch.Patch(self)
        p.read(filePath)
        self._setPatch(p)
        self.setWindowFilePath(filePath)
        self.setWindowTitle(QFileInfo(filePath).fileName())
        self.prefs.setValue('lastFilePath', filePath)
        if usedDialog:
            self.prefs.setValue('lastFileOpenPath', filePath)

    # General app stuff

    def readPrefs(self):
        self.resize(self.prefs.value('size', type=QSize))
        #
        state = util.int_list(self.prefs.value('outerSplitter'))
        if state:
            self.ui.outerSplitter.setSizes(state)
        x = self.prefs.value('innerSplitterShown', type=bool, defaultValue=False)
        self.ui.innerSplitter.setVisible(x)
        innerState = util.int_list(self.prefs.value('innerSplitter'))
        if innerState:
            self.ui.innerSplitter.setSizes(innerState)
        #
        x = self.prefs.value('simulatorShown', type=bool, defaultValue=True)
        self.ui.simulator.setVisible(x)
        x = self.prefs.value('activityLogShown', type=bool, defaultValue=True)
        self.ui.activityLog.setVisible(x)
        x = self.prefs.value('bindingPropertiesShown', type=bool, defaultValue=True)
        self.ui.bindingPropertiesScroller.setVisible(x)
        QTimer.singleShot(0, self.checkSimulatorHeight)
        #
        x = self.prefs.value('toolButtonStyle', type=str)
        if x == 'iconOnly':
            self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        elif x == 'iconPlusName':
            self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        else:
            self.toolbar.setToolButtonStyle(Qt.ToolButtonIconOnly)
        #
        self.prefs.beginGroup('InputPorts')
        for portName in self.prefs.childGroups():
            self.prefs.beginGroup(portName)
            enabled = self.prefs.value('enabled', type=bool)
            self.setInputPortEnabled(portName, enabled)
            self.prefs.endGroup()
        self.prefs.endGroup()
        #
        filePath = self.prefs.value('lastFilePath')
        if filePath and QFileInfo(filePath).isFile():
            self.open(filePath)
        else:
            self.new()

    def writePrefs(self):
        was = self.prefs.setAutoSave(False)
        self.prefs.setValue('size', self.size())
        self.prefs.setValue('outerSplitter', self.ui.outerSplitter.sizes())
        self.prefs.setValue('innerSplitter', self.ui.innerSplitter.sizes())
        x = self.toolbar.toolButtonStyle()
        if x == Qt.ToolButtonIconOnly:
            y = 'iconOnly'
        elif x == Qt.ToolButtonTextUnderIcon:
            y = 'iconPlusName'
        self.prefs.setValue('toolButtonStyle', y)
        self.prefs.setAutoSave(was)
        self.prefs.sync()

    def showAbout(self):
        version = 1.1
        QMessageBox.about(self, tr("About PKMidiCron"),
                          tr("""PKMidiCron %s\nvedanamedia.com""" % version))


    def showPreferences(self):
        if self.prefsDialog is None:
            self.prefsDialog = preferencesdialog.PreferencesDialog(self)
            self.prefsDialog.exec()
            self.prefsDialog = None

    def toggleMainWindow(self):
        x = not self.isVisible()
        self.setVisible(x)
        self.prefs.setValue("MainWindowShown", x)

    def toggleSimulator(self):
        x = not self.ui.simulator.isVisible()
        self.ui.simulator.setVisible(x)
        if x:
            sizes = self.ui.innerSplitter.sizes()
            if sizes[0] == 0:
                h = self.ui.simulator.sizeHint().height()
                self.ui.innerSplitter.setSizes([h, sizes[1], sizes[2]])
        self.prefs.setValue('simulatorShown', x)
        self.checkInnerSplitter(x)

    def toggleLog(self):
        x = not self.ui.activityLog.isVisible()
        self.ui.activityLog.setVisible(x)
        if x:
            sizes = self.ui.innerSplitter.sizes()
            if sizes[1] == 0:
                h = self.ui.activityLog.sizeHint().height()
                self.ui.innerSplitter.setSizes([sizes[0], h, sizes[2]])
        self.prefs.setValue('activityLogShown', x)
        self.checkInnerSplitter(x)

    def toggleBindingProperties(self):
        x = not self.ui.bindingPropertiesScroller.isVisible()
        self.ui.bindingPropertiesScroller.setVisible(x)
        if x:
            sizes = self.ui.innerSplitter.sizes()
            if sizes[2] == 0:
                h = self.ui.bindingPropertiesScroller.sizeHint().height()
                self.ui.innerSplitter.setSizes([sizes[0], sizes[1], h])
        self.prefs.setValue('bindingPropertiesShown', x)
        self.checkInnerSplitter(x)

    def checkSimulatorHeight(self):
        x = self.ui.simulator.isVisible()
        y = self.ui.activityLog.isVisible()
        z = self.ui.bindingPropertiesScroller.isVisible()
        if x and (y or z):
            sizes = self.ui.innerSplitter.sizes()
            if sizes[0] > self.ui.simulator.sizeHint().height():
                sizes[0] = self.ui.simulator.sizeHint().height()
                self.ui.innerSplitter.setSizes(sizes)        

    def checkInnerSplitter(self, on=False):
        x = self.ui.simulator.isVisible()
        y = self.ui.activityLog.isVisible()
        z = self.ui.bindingPropertiesScroller.isVisible()
        if on or x or y or z:
            self.ui.innerSplitter.show()
            if self.ui.innerSplitter.width() == 0:
                w1 = self.ui.bindingsList.sizeHint().width()
                self.ui.outerSplitter.setSizes([w1, 400])
            self.prefs.setValue('innerSplitterShown', True)
        else:
            self.ui.innerSplitter.hide()
            self.prefs.setValue('innerSplitterShown', False)
        QTimer.singleShot(0, self.checkSimulatorHeight)

    # Functionality

    def addBinding(self, binding=None):
        if binding is None or type(binding) == bool:
            binding = self.patch.addBinding()
        bindinglistitem.BindingListItem(self.ui.bindingsList, binding)
        return binding
        
    def removeSelectedBinding(self):
        items = self.ui.bindingsList.selectedItems()
        if not items:
            return
        iItem = self.ui.bindingsList.row(items[0])
        item = self.ui.bindingsList.takeItem(iItem)
        self.patch.removeBinding(item.binding)

    def onBindingSelectionChanged(self, x, y):
        if x.indexes():
            self.ui.actionDeleteBinding.setEnabled(True)
            item = self.ui.bindingsList.item(x.indexes()[0].row())
            self.ui.bindingProperties.init(item.binding)
        elif y.indexes():
            self.ui.actionDeleteBinding.setEnabled(False)
            self.ui.bindingProperties.clear()

    def clearActivityLog(self):
        self.ui.activityLog.clearContents()
        self.ui.activityLog.setRowCount(0)
        self.ui.actionClearLog.setEnabled(False)

    def setInputPortEnabled(self, name, x):
        self.collector.setPortEnabled(name, x)

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
        self.ui.actionClearLog.setEnabled(True)
        for col, item in enumerate(items):
            self.ui.activityLog.setItem(rows, col, items[col])
        if bottom:
            QTimer.singleShot(0, self.ui.activityLog.scrollToBottom)
        self.patch.onMidiMessage(portName, midi)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, mainwindow):
        super().__init__(mainwindow)
        self.setIcon(QIcon(QPixmap(':/icon.png')))

        self.menu = QMenu(mainwindow)
        self.showAction = self.menu.addAction(tr("Main Window"))
        self.showAction.triggered.connect(mainwindow.toggleMainWindow)
        self.quitAction = self.menu.addAction(tr("Quit"))
        self.quitAction.triggered.connect(QApplication.quit)

        self.setContextMenu(self.menu)



import sys
import rtmidi
from .pyqt_shim import *
from . import util, engine, mainwindow_form, bindinglistitem, preferencesdialog_form, preferencesdialog
from .ports import inputs
from .util import refs


CONFIRM_SAVE = False


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
        self.firstMessage = True
        self.originalPaths = sys.path

        # don't auto list here because we will add post explicitly using ports().portAdded
        self.enableAllInputs = False
        self.collector = util.CollectorBin(parent=self, autolist=False)
        self.collector.message.connect(self.onMidiMessage)
        inputs().portAdded.connect(self.onInputPortAdded)
        inputs().portAdded.connect(self.onInputPortRemoved)
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
        spacer.setAttribute(Qt.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        self.toolbar.addAction(self.ui.actionAddBinding)
        self.ui.actionAddBinding.setIcon(QIcon(':/icons/retina/plus.png'))
        self.toolbar.addAction(self.ui.actionDeleteBinding)
        self.ui.actionDeleteBinding.setIcon(QIcon(':/icons/retina/multiply.png'))
        spacer = QWidget(self.toolbar)
        spacer.setAttribute(Qt.WA_TransparentForMouseEvents)
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.toolbar.addWidget(spacer)
        spacer = QWidget(self.toolbar)
        spacer.setAttribute(Qt.WA_TransparentForMouseEvents)
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
        self.ui.actionExit.triggered.connect(self.onQuit)
        self.ui.actionToggleBindings.triggered.connect(self.toggleBindings)
        self.ui.actionToggleSimulator.triggered.connect(self.toggleSimulator)
        self.ui.actionToggleLog.triggered.connect(self.toggleLog)
        self.ui.actionToggleBindingProperties.triggered.connect(self.toggleBindingProperties)
        self.ui.actionToggleMainWindow.triggered.connect(self.toggleMainWindow)
        self.ui.actionShowHelp.triggered.connect(self.showHelp)

        # Init

        self.patch = None
        self.prefs = prefs and prefs or QSettings()
        self.readPrefs()

    def cleanup(self):
        """ close and delete all editors for shutdown """
        if self.patch:
            for b in self.patch.bindings:
                for a in b.actions:
                    if hasattr(a, 'editor') and a.editor:
                        a.editor.close()
                        a.editor = None

    ## Patch mgmt

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

    def onQuit(self):
        if self.confirmSave():
            self.writePrefs()
            QApplication.quit()

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
        self._setPatch(engine.Patch(), force=True)

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
        self.ui.simulator.init(self.patch.simulator)
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
        else:
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
            return False
        self.prefs.setValue('lastFileSavePath', filePath)
        self.save(filePath)
        return True

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
        p = engine.Patch(self)
        p.read(filePath)
        self._setPatch(p)
        self.setWindowFilePath(filePath)
        self.setWindowTitle(QFileInfo(filePath).fileName())
        self.prefs.setValue('lastFilePath', filePath)
        if usedDialog:
            self.prefs.setValue('lastFileOpenPath', filePath)

    ## Generic App Stuff

    def readPrefs(self):
        self.resize(self.prefs.value('size', type=QSize, defaultValue=QSize(600, 400)))
        #
        state = util.int_list(self.prefs.value('outerSplitter'))
        if state:
            self.ui.outerSplitter.setSizes(state)
            if state[0] == 0:
                self.ui.bindingsList.hide()
        #
        x = self.prefs.value('innerSplitterShown', type=bool, defaultValue=True)
        self.ui.innerSplitter.setVisible(x)
        innerState = util.int_list(self.prefs.value('innerSplitter'))
        if innerState:
            self.ui.innerSplitter.setSizes(innerState)
        #
        x = self.prefs.value('bindingsShown', type=bool, defaultValue=False)
        self.ui.bindingsList.setVisible(x)
        x = self.prefs.value('simulatorShown', type=bool, defaultValue=False)
        self.ui.simulator.setVisible(x)
        x = self.prefs.value('activityLogShown', type=bool, defaultValue=True)
        self.ui.activityLog.setVisible(x)
        x = self.prefs.value('bindingPropertiesShown', type=bool, defaultValue=False)
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
        self.enableAllInputs = self.prefs.value('EnableAllInputs', defaultValue=True, type=bool)
        self.prefs.beginGroup('InputPorts')
        names = self.prefs.childKeys()
        for x in inputs().names():
            if not x in names:
                names.append(x)
        for portName in names:
            self.prefs.beginGroup(portName)
            if self.enableAllInputs:
                enabled = True
            else:
                enabled = self.prefs.value('enabled', type=bool, defaultValue=True)
            self.setInputPortEnabled(portName, enabled)
            self.prefs.endGroup()
        self.prefs.endGroup()
        #
        self.prefs.beginGroup('Python/Paths')
        sys.path = self.originalPaths
        for i in self.prefs.childKeys():
            path = self.prefs.value(i, type=str)
            sys.path.append(path)
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
        self.prefs.setValue('EnableAllInputs', bool(self.enableAllInputs))
        self.prefs.setAutoSave(was)
        self.prefs.sync()

    ## Views

    def showAbout(self):
        version = 1.1
        QMessageBox.about(self, tr("About PKMidiCron"),
                          tr("""PKMidiCron %s\nvedanamedia.com""" % version))

    def showHelp(self):
        QDesktopServices.openUrl(QUrl('http://vedanamedia.com/products/pkmidicron'))

    def showPreferences(self):
        if self.prefsDialog is None:
            self.prefsDialog = preferencesdialog.PreferencesDialog(self)
        self.prefsDialog.exec()

    def toggleMainWindow(self):
        w = QApplication.activeWindow()
        if w == self or w is None:
            self.setVisible(not self.isVisible())
        elif w:
            w.close()
        
    def closeEvent(self, e):
        self.trayIcon.showHello()
        self.prefs.setValue("MainWindowShown", False)
        
    def showEvent(self, e):
        self.prefs.setValue("MainWindowShown", True)

    def isLastView(self, x):
        """ Return True if all other views are hidden and this one is shown,
        meaning that if this one is shown then the mainwindow would be blank. """
        if not x.isVisible():
            return False
        w = [self.ui.simulator,
             self.ui.activityLog,
             self.ui.bindingPropertiesScroller,
             self.ui.bindingsList]
        w.remove(x)
        any = False
        for i in w:
            if i.isVisible():
                any = True
        return not any

    def showBindingsList(self):
        """ ensure not visible but collapsed """
        if not self.ui.bindingsList.isVisible():
            self.toggleBindings()
        else:
            sizes = self.ui.outerSplitter.sizes()
            if sizes[0] == 0:
                sizes[0] = self.ui.bindingsList.sizeHint().width()
                self.ui.outerSplitter.setSizes(sizes)

    def toggleBindings(self):
        if self.isLastView(self.ui.bindingsList):
            return
        x = self.ui.simulator.isVisible()
        y = self.ui.activityLog.isVisible()
        z = self.ui.bindingPropertiesScroller.isVisible()
        if not x and not y and not z and self.ui.bindingsList.isVisible():
            return
        x = not self.ui.bindingsList.isVisible()
        self.ui.bindingsList.setVisible(x)
        if x:
            sizes = self.ui.outerSplitter.sizes()
            if sizes[0] == 0:
                h = self.ui.bindingsList.sizeHint().height()
                self.ui.outerSplitter.setSizes([h, sizes[1]])
        self.prefs.setValue('bindingsShown', x)

    def toggleSimulator(self):
        if self.isLastView(self.ui.simulator):
            return
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
        if self.isLastView(self.ui.activityLog):
            return
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
        if self.isLastView(self.ui.bindingPropertiesScroller):
            return
        x = not self.ui.bindingPropertiesScroller.isVisible()
        self.ui.bindingPropertiesScroller.setVisible(x)
        if x:
            self.showBindingProperties()
        self.prefs.setValue('bindingPropertiesShown', x)
        self.checkInnerSplitter(x)

    def showBindingProperties(self):
        """ ensure not visible but collapsed """
        w = self.ui.bindingPropertiesScroller
        if not w.isVisible():
            w.setVisible(True)
        sizes = self.ui.innerSplitter.sizes()
        if sizes[2] == 0:
            m = (sizes[0] + sizes[1]) / .3
            sizes[2] = w.sizeHint().height() + m
            self.ui.innerSplitter.setSizes(sizes)

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
        """ Hide entire splitter of all children are hidden to remove handle """
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

    ## MIDI Ports

    def setEnableAllInputs(self, on):
        self.enableAllInputs = on
        for name in inputs().names():
            if on:
                enabled = True
            else:
                enabled = self.prefs.value('InputPorts/%s/enabled' % name, type=bool, defaultValue=True)
            self.setInputPortEnabled(name, enabled)

    def setInputPortEnabled(self, name, x):
        """ called from prefs, port added / removed """
        self.collector.setPortEnabled(name, x)
        
    def onInputPortAdded(self, portName):
        """ called from ports.py """
        if self.enableAllInputs:
            enabled = True
        else:
            self.prefs.beginGroup('InputPorts/')
            self.prefs.beginGroup(portName)
            enabled = self.prefs.value('enabled', type=bool, defaultValue=True)
            self.prefs.endGroup()
            self.prefs.endGroup()
        self.setInputPortEnabled(portName, enabled)

    def onInputPortRemoved(self, portName):
        """ called from ports.py """
        self.setInputPortEnabled(portName, False)

    ## Functionality

    def addBinding(self, binding=None):
        self.showBindingsList()
        if binding is None or type(binding) == bool:
            binding = self.patch.addBinding()
        item = bindinglistitem.BindingListItem(self.ui.bindingsList, binding)
        item.binding = binding
        self.ui.actionDeleteBinding.setEnabled(True)

    def removeSelectedBinding(self):
        items = self.ui.bindingsList.selectedItems()
        if not items: return
        item = items[0]
        binding = item.binding
        self.ui.bindingsList.takeItem(self.ui.bindingsList.row(item))
        item.cleanup()
        self.patch.removeBinding(binding)

    def onBindingSelectionChanged(self, x, y):
        if x.indexes():
            self.ui.actionDeleteBinding.setEnabled(True)
            item = self.ui.bindingsList.item(x.indexes()[0].row())
            self.ui.bindingProperties.init(item.binding)
            self.showBindingProperties()
        elif y.indexes():
            self.ui.actionDeleteBinding.setEnabled(False)
            self.ui.bindingProperties.clear()

    def clearActivityLog(self):
        self.ui.activityLog.clearContents()
        self.ui.activityLog.setRowCount(0)
        self.ui.actionClearLog.setEnabled(False)

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
        f = QFont(self.ui.activityLog.font())
        if QApplication.platformName() == 'windows':
            f.setPointSize(8)
        for col, item in enumerate(items):
            item.setFont(QFont(f))
            self.ui.activityLog.setItem(rows, col, items[col])
        if self.firstMessage:
            self.ui.activityLog.resizeColumnsToContents()
            self.ui.activityLog.horizontalHeader().setStretchLastSection(True)
            self.firstMessage = False
        if bottom:
            QTimer.singleShot(0, self.ui.activityLog.scrollToBottom)
        self.patch.onMidiMessage(portName, midi)


class TrayIcon(QSystemTrayIcon):
    def __init__(self, mainwindow):
        super().__init__(mainwindow)
        self.setIcon(QIcon(QPixmap(':/icon.png')))
        self.hasShownHello = False

        self.menu = QMenu(mainwindow)
        self.showAction = self.menu.addAction(tr("Main Window"))
        self.showAction.triggered.connect(mainwindow.toggleMainWindow)
        self.quitAction = self.menu.addAction(tr("Quit"))
        self.quitAction.triggered.connect(mainwindow.onQuit)

        if QApplication.platformName() == 'windows':
            self.activated.connect(self.iconActivated)
        self.messageClicked.connect(mainwindow.show)
        self.setContextMenu(self.menu)
        
    def iconActivated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.parent().toggleMainWindow()

    def showHello(self):
        if not self.hasShownHello:
            self.showMessage("Here I am!", "PKMidiCron will now run in the tray. Click the tray icon again to show the main window.")
            self.hasShownHello = True


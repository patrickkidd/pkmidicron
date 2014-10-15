




class MainWindow(QWidget):
    def __init__(self, settings=None, parent=None):
        QWidget.__init__(self, parent)
        self.setMinimumWidth(875)
        self.resize(600, 200)

        self.bindings = []
        device = rtmidi.RtMidiIn()
        self.settings = settings and settings or QSettings()

        self.splitter = QSplitter(Qt.Vertical, self)

        
        self.collector = CollectorBin(self)
        self.collector.message.connect(self.onMidiMessage)
        self.collector.start()

        self.simulator = Simulator()
        self.simulator.received.connect(self.onMidiMessage)
        self.tabs = QTabWidget(self)
        self.tabs.setTabBar(EmptyTabBar())
        self.tabs.addTab(self.simulator, 'Simulator')

        self.activityCount = 0
        self.activityLog = QTextEdit()
        self.activityLog.setReadOnly(True)

        self.bindingsContainer = QTabWidget(self)
        self.bindingsContainer.setTabBar(EmptyTabBar())
        self.bindingsScroller = QScrollArea(self)
        self.bindingsScroller.setFrameShape(QFrame.NoFrame)
        self.bindingsScroller.setWidgetResizable(True)
        self.bindingsWidget = QWidget()
        self.bindingsScroller.setWidget(self.bindingsWidget)
        self.bindingsContainer.addTab(self.bindingsScroller, 'Bindings')

        self.addButton = QPushButton("+", self)
        self.addButton.setMaximumSize(50, 50)
        self.addButton.clicked.connect(self.addBinding)

        Layout = QVBoxLayout()
        Layout.addWidget(self.tabs, 0)
        self.splitter.addWidget(self.activityLog)
        #
        self.bindingsLayout = QVBoxLayout()
        self.bindingsLayout.setContentsMargins(0, 0, 0, 0)
        self.bindingsLayout.setSpacing(5)
        self.bindingsWidget.setLayout(self.bindingsLayout)
        setBackgroundColor(self.bindingsWidget, QColor('#E5E5E5'))
        self.bindingsLayout.addStretch(10)
        self.splitter.addWidget(self.bindingsContainer)
        Layout.addWidget(self.splitter, 1)
        #
        self.ctlLayout = QHBoxLayout()
        self.ctlLayout.setContentsMargins(0, 0, 0, 0)
        self.ctlLayout.setSpacing(0)
        self.ctlLayout.addWidget(self.addButton)
        self.ctlLayout.addStretch(10)
        Layout.addLayout(self.ctlLayout, 0)
        #
        self.setLayout(Layout)

        ## init
        
        self.readSettings(self.settings)

    def __del__(self):
        self.writeSettings(self.settings)
        self.collector.stop()

    def readSettings(self, settings):
        self.resize(settings.value('size', type=QSize))
        i = 0
        settings.beginGroup('bindings')
        keys = settings.childGroups()
        found = True
        while found:
            key = str(i)
            settings.beginGroup(key)
            found = len(settings.allKeys()) > 0
            if found:
                b = self.addBinding(save=False)
                b.readSettings(settings)
            settings.endGroup()
            i += 1
        settings.endGroup()
        settings.beginGroup('simulator')
        self.simulator.readSettings(settings)
        settings.endGroup()

    def writeBindingsSettings(self, settings=None):
        if settings is None:
            settings = self.settings        
        settings.remove('bindings')
        settings.beginGroup('bindings')
        for i, b in enumerate(self.bindings):
            settings.beginGroup(str(i))
            b.writeSettings(settings)
            settings.endGroup()
        settings.endGroup()
        settings.beginGroup('simulator')
        if hasattr(self, 'simulator'): # exceptions..
            self.simulator.writeSettings(settings)
        settings.endGroup()

    def writeSettings(self, settings=None):
        if settings is None:
            settings = self.settings
        settings.setValue('size', self.size())
        self.writeBindingsSettings()
        settings.sync()
        
    def onMidiMessage(self, portName, midi):
        s = midi.__str__().replace('<', '').replace('>', '')
        self.activityCount += 1
        self.activityLog.append('#%i %s: %s' % (self.activityCount, portName, midi))
        for b in self.bindings:
            b.match(portName, midi)

    def addBinding(self, save=True):
        b = Binding(self.bindingsWidget)
        self.bindingsLayout.insertWidget(self.bindingsLayout.count()-1, b)
        b.changed.connect(self.writeBindingsSettings)
        self.bindings.append(b)
        self.settings.beginGroup('bindings/%s' % (len(self.bindings) - 1))
        b.writeSettings(self.settings)
        self.settings.endGroup()
        b.removeMe.connect(self.removeBinding)
        if save:
            self.settings.sync()
        return b
        
    def removeBinding(self, b):
        self.bindingsLayout.removeWidget(b)
        self.bindings.remove(b)
        b.setParent(None)


from pyqt_shim import *
from .binding import *
from .simulator import *
import rtmidi

class MainWindow(QWidget):
    def __init__(self, settings=None, parent=None):
        QWidget.__init__(self, parent)
        self.setMinimumWidth(875)

        self.bindings = []
        self.settings = settings and settings or QSettings()

        self.resize(600, 200)
        device = rtmidi.RtMidiIn()

        self.collector = CollectorBin(self)
        self.collector.message.connect(self.onMidiMessage)
        self.collector.start()

        self.simulatorTabs = QTabWidget(self)
        self.simulator = Simulator()
        self.simulator.received.connect(self.onMidiMessage)
        self.simulatorTabs.addTab(self.simulator, '&Simulator')

        self.activityTabs = QTabWidget(self)
        self.activityLog = QTextEdit()
        self.activityLog.setReadOnly(True)
        self.activityTabs.addTab(self.activityLog, "&Activity")

        self.bindingsScroller = QScrollArea(self)
        self.bindingsScroller.setWidgetResizable(True)
        self.bindingsWidget = QWidget()
        self.bindingsScroller.setWidget(self.bindingsWidget)

        self.addButton = QPushButton("+", self)
        self.addButton.setMaximumSize(50, 50)
        self.addButton.clicked.connect(self.addBinding)

        Layout = QVBoxLayout()
        Layout.addWidget(self.simulatorTabs, 0)
        Layout.addWidget(self.activityTabs, 1)
        #
        self.bindingsLayout = QVBoxLayout()
        self.bindingsLayout.setContentsMargins(0, 0, 0, 0)
        self.bindingsLayout.setSpacing(5)
        self.bindingsWidget.setLayout(self.bindingsLayout)
        self.bindingsLayout.addStretch(10)
        Layout.addWidget(self.bindingsScroller, 1)
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
        self.activityLog.append('%s: %s' % (portName, midi))
        for b in self.bindings:
            b.match(portName, midi)

    def addBinding(self, save=True):
        b = Binding(self.bindingsWidget)
        self.bindingsLayout.insertWidget(0, b)
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


class CollectorBin(QObject, rtmidi.CollectorBin):

    message = pyqtSignal(str, rtmidi.MidiMessage)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        rtmidi.CollectorBin.__init__(self, self._callback)

    def _callback(self, collector, msg):
        self.message.emit(collector.portName, msg)


class Collector(QThread):

    midi = pyqtSignal(rtmidi.MidiMessage)

    def __init__(self, parent):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.device = None
        self.quit = False

    def setDevice(self, device):
        self.mutex.lock()
        shouldStart = self.device is None
        self.device = device
        self.device.ignoreTypes(True, False, True)
        self.mutex.unlock()
        if shouldStart:
            self.start()
    
    def run(self):
        while not self.quit:
            if self.mutex.tryLock(250):
                msg = self.device.getMessage(250)
                self.mutex.unlock()
                if not msg is None:
                    self.midi.emit(msg)


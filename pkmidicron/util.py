import rtmidi
from . import pyqt_shim as qt
from .pyqt_shim import QObject, QThread, pyqtSignal

ANY_TEXT = '** ANY **'
ALL_TEXT = '** ALL **'

def setBackgroundColor(w, c):
    if not hasattr(w, '_orig_palette'):
        w._orig_palette = w.palette()
    p = qt.QPalette(w.palette())
    p.setColor(qt.QPalette.Background, c);
    w.setAutoFillBackground(True)
    w.setPalette(p)


def clearBackgroundColor(w):
    if not hasattr(w, '_orig_palette'):
        return
    w.setPalette(w._orig_palette)
    del w._orig_palette
    w.setAutoFillBackground(False)



class EmptyTabBar(qt.QTabBar):
    def __init__(self, parent=None):
        qt.QTabBar.__init__(self, parent)

    def paintEvent(self, e):
        pass



class Led(qt.QFrame):
    def __init__(self, parent=None):
        qt.QFrame.__init__(self, parent)
        h = self.fontMetrics().height()
        self.setMinimumSize(h * 2, h)
        self._color = qt.Qt.red
        self.timer = qt.QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.off)
        self.isOn = False
        self.setFrameStyle(qt.QFrame.Box)

    def setColor(self, c):
        self._color = c
        if self.isOn:
            setBackgroundColor(self, c)

    def off(self):
        clearBackgroundColor(self)
        self.isOn = False

    def on(self, ms=-1):
        setBackgroundColor(self, self._color)
        self.isOn = True
        if ms > -1:
            self.timer.stop()
            self.timer.start(ms)

    def flash(self):
        self.on(100)


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

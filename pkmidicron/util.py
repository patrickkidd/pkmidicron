import rtmidi
from . import pyqt_shim as qt
from .pyqt_shim import QObject, QThread, pyqtSignal

ANY_TEXT = '** ANY **'
ALL_TEXT = '** ALL **'
NONE_TEXT = '** NONE **'

MSG_NOTE_ON = 0
MSG_NOTE_OFF = 1
MSG_CC = 2
MSG_AFTERTOUCH = 3
MSG_ALL_NOTES_OFF = 127

ACTION_SEND_MESSAGE = 0
ACTION_RUN_PROGRAM = 1
ACTION_OPEN_FILE = 2

def midiTypeString(midi):
    if midi.isNoteOn():
        return 'Note On'
    elif midi.isNoteOff():
        return 'Note Off'
    elif midi.isController():
        return 'CC'
    elif midi.isAftertouch():
        return 'Aftertouch'
    elif midi.isPitchWheel():
        return 'Pitch Wheel'
    elif midi.isProgramChange():
        return 'Program Change'
    elif midi.isChannelPressure():
        return 'Channel Pressure'
    else:
        return 'unknown: %s' % midi

def midiDataSummary(midi):
    if midi.isNoteOn():
        return '%s (%s), %s' % (midi.getNoteNumber(),
                                rtmidi.MidiMessage.getMidiNoteName(midi.getNoteNumber(), True, True, 3),
                                midi.getVelocity())
    elif midi.isNoteOff():
        return '%s' % midi.getNoteNumber()
    elif midi.isController():
        return '#%s, %s' % (midi.getControllerNumber(), midi.getControllerValue())
    elif midi.isAftertouch():
        return '%s (%s), %s' % (midi.getNoteNumber(),
                           rtmidi.MidiMessage.getMidiNoteName(midi.getNoteNumber(), True, True, 3),
                           midi.getAfterTouchValue())
    elif midi.isPitchWheel():
        return '%s' % midi.getPitchWheelValue()
    elif midi.isProgramChange():
        return '%s' % midi.getProgramChangeNumber()
    elif midi.isChannelPressure():
        return '%s' % midi.getChannelPressureValue()
    


class HR(qt.QWidget):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self, parent)

    def paintEvent(self, e):
        p = QPainter(e)
        
        y = self.height() / 2
        line = QLine(0, y, self.width(), y)
        p.setPen(Qt.black)
        p.drawLine(line)

class CollapsableBox(qt.QFrame):
    def __init__(self, title, parent=None):
        qt.QFrame.__init__(self, parent)

        self.isCollapsed = False

        self.header = qt.QWidget(self)
        self.header.setFixedHeight(40)
        self.headerButton = qt.QPushButton('-', self)
        self.headerButton.setFixedWidth(20)
        self.headerLabel = qt.QLabel(title, self)

        HeaderLayout = qt.QHBoxLayout()
        HeaderLayout.addWidget(self.headerButton)
        HeaderLayout.addWidget(self.headerLabel)
        self.header.setLayout(HeaderLayout)

        self.content = qt.QWidget()

        Layout = qt.QVBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.header, 0)
        Layout.addWidget(self.content, 1)
        self.setLayout(Layout)

        self.headerButton.clicked.connect(self.toggle)

    def mouseDoubleClickEvent(self, e):
        self.toggle()

    def toggle(self):
        if self.isCollapsed:
            self.content.show()
            self.headerButton.setText('-')
            self.isCollapsed = False
        else:
            self.content.hide()
            self.headerButton.setText('+')
            self.isCollapsed = True



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
#        self.setFrameStyle(qt.QFrame.Box)

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

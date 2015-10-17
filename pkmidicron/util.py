import sys
import time
from traceback import print_stack
import rtmidi
from . import pyqt_shim as qt
from .pyqt_shim import *

ANY_TEXT = '** ANY **'
ALL_TEXT = '** ALL **'
NONE_TEXT = '** NONE **'

MSG_NOTE_ON = 0
MSG_NOTE_OFF = 1
MSG_CC = 2
MSG_AFTERTOUCH = 3
MSG_ANY = 4
MSG_ALL = 5
MSG_ALL_NOTES_OFF = 127

ACTION_SEND_MESSAGE = 0
ACTION_RUN_PROGRAM = 1
ACTION_OPEN_FILE = 2
ACTION_RUN_SCRIPT = 3

STATE_COMPILED = 1
STATE_EDITED = 2
STATE_ERROR = 3

EXTENSIONS = ['pmc']
FILE_TYPES = "PKMidiCron files (%s)" % ','.join(['*.'+i for i in EXTENSIONS])

VERSION_MAJOR = 1
VERSION_MINOR = 1
VERSION_MICRO = 0
VERSION = '%s.%s.%s' % (VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO)
VERSION_URL = QUrl('http://vedanamedia.com/products/pkmidicron/version.txt')

def verint(a, b, c):
    print('verint', a, b, c, type(a), type(b), type(c))
    return (a << 24) | (b << 16) | c

def updateAvailable(text):
    text = text.strip()
    major, minor, micro = [int(i) for i in text.split('.')]
    there = verint(major, minor, micro)
    here = verint(VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO)
    return here < there
    

def refs(o,s=''):
    print('refs: ', s, sys.getrefcount(o), o)

class Application(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def event(self, e):
        if e.type() == QEvent.FileOpen:
            filePath = e.file()
            if QFileInfo(filePath).suffix() in EXTENSIONS:
                if QFileInfo(filePath).exists():
                    for w in self.topLevelWidgets():
                        if isinstance(w, QMainWindow):
                            w.open(filePath)
                    return True
        return super().event(e)


class CollectorBin(QObject, rtmidi.CollectorBin):

    message = pyqtSignal(str, rtmidi.MidiMessage)

    def __init__(self, **kwargs):
        kwargs['callback'] = self.callback
        kwargs['autolist'] = False
        super().__init__(**kwargs)
        from .ports import inputs
        inputs().portAdded.connect(self._add)
        inputs().portRemoved.connect(self._remove)

    def callback(self, collector, msg):
        self.message.emit(collector.portName, msg)

    def setPortEnabled(self, name, x):
        if x:
            self._add(name)
        else:
            self._remove(name)

    def _add(self, name):
        self.addCollector(name)

    def _remove(self, name):
        self.removeCollector(name)


class Button(QPushButton):
    def __init__(self, path, parent=None):
        QPushButton.__init__(self, parent)
        self.setIcon(QIcon(QPixmap(path)))

#    def paintEvent(self, e):
#        if 
#        p = QPainter(



def int_list(x):
    if type(x) == list:
        return [int(i) for i in x]
    else:
        return x

class Settings(QSettings):
    def __init__(self, *args):
        super().__init__(*args)
        self._autoSave = False

    def autoSave(self):
        return self._autoSave

    def setAutoSave(self, x):
        self._autoSave = bool(x)
        return self._autoSave

    autoSave = pyqtProperty(bool, autoSave, setAutoSave)

    def setValue(self, *args, **kwargs):
        super().setValue(*args, **kwargs)
        if self.autoSave:
            self.sync()

class ScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)

    def eventFilter(self, o, e):
        if o and o == self.widget() and e.type() == QEvent.Resize:
            if self.horizontalScrollBarPolicy() == Qt.ScrollBarAlwaysOff:
                w = self.widget().minimumSizeHint().width() + self.verticalScrollBar().width()
                self.setMinimumWidth(w + 2)
            if self.verticalScrollBarPolicy() == Qt.ScrollBarAlwaysOff:
                w = self.widget().minimumSizeHint().height() + self.horizontalScrollBar().height()
                self.setMinimumHeight(w + 2)
        return super().eventFilter(o, e)



class ListWidget(QListWidget):

#    deleted = pyqtSignal(BindingListItem)

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



def _openPort(name):
    print('openPort:', name)
    device = rtmidi.RtMidiOut()
    for i in range(device.getPortCount()):
        if device.getPortName(i) == name:
            device.openPort(i)
            return device


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
        return '%s (%s)' % (midi.getNoteNumber(),
                                rtmidi.MidiMessage.getMidiNoteName(midi.getNoteNumber(), True, True, 3))
    elif midi.isController():
        s = midi.getControllerName(midi.getControllerNumber())
        if s:
            return '#%s (%s), %s' % (midi.getControllerNumber(), s, midi.getControllerValue())
        else:
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




class ClickToEdit(QLineEdit):

    clicked = pyqtSignal()

    def __init__(self, parent=None, flashColor=None):
        QLineEdit.__init__(self, parent)
        self.clickTimer = QTimer(parent)
        self.clickTimer.timeout.connect(self.clickTimerTimeout)
        self.lastRelease = 0
        self.disableClick = False
        self.setFocusPolicy(Qt.NoFocus)

        self.textAnimation = QPropertyAnimation(self, "textColor", self)
        self.textAnimation.setDuration(500)
        self.defaultFlashColor = flashColor and QColor(flashColor) or QColor("red")
        self.textAnimation.setStartValue(self.defaultFlashColor)
        self.textAnimation.setEndValue(self.palette().color(QPalette.Text))
        self.textAnimation.setEasingCurve(QEasingCurve.InOutQuad)

    def clickTimerTimeout(self):
        self.clicked.emit()
        self.clickTimer.stop()

    def mouseReleaseEvent(self, e):
        x = time.time()
        if x - self.lastRelease > .1: # single double click
            self.clickTimer.stop()
            self.clickTimer.start(110)
            e.accept()
        self.lastRelease = x

    def mouseDoubleClickEvent(self, e):
        self.clickTimer.stop()
        if self.disableClick:
            return
        if self.isReadOnly():
            self.setReadOnly(False)
            self.setFocus(Qt.MouseFocusReason)
            self.selectAll()

    def focusOutEvent(self, e):
        self.setReadOnly(True)
        self.deselect()

    def keyReleaseEvent(self, e):
        if e.key() == Qt.Key_Enter or e.key() == Qt.Key_Return:
            self.setReadOnly(True)

    def setDisableClick(self, x):
        self.disableClick = x

    @pyqtProperty(QColor)
    def textColor(self):
        return self.palette().text().color()

    @textColor.setter
    def textColor(self, x):
        if x.__class__ == QBrush:
            x = x.color()
        p = self.palette()
        p.setColor(QPalette.Text, x)
        self.setPalette(p)
        
    def flash(self, color=None):
        if color:
            self.textAnimation.setStartValue(color)
        else:
            self.textAnimation.setStartValue(self.defaultFlashColor)
        self.textAnimation.stop()
        self.textAnimation.start()


class HR(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

    def paintEvent(self, e):
        p = QPainter(e)
        
        y = self.height() / 2
        line = QLine(0, y, self.width(), y)
        p.setPen(Qt.black)
        p.drawLine(line)

class CollapsableBox(QFrame):
    def __init__(self, title, parent=None):
        QFrame.__init__(self, parent)

        self.isCollapsed = False
        self.image = QImage(":/box-bg-2.jpg")

        self.header = QWidget(self)
        self.header.setFixedHeight(45)
        self.headerButton = QPushButton('-', self)
        self.headerButton.setFixedWidth(20)
        self.headerButton.hide()
        if type(title) == QPixmap:
            self.headerLabel = QLabel('', self)
            self.headerLabel.setPixmap(title)
        else:
            self.headerLabel = QLabel(title, self)

        HeaderLayout = QHBoxLayout()
        HeaderLayout.addWidget(self.headerButton)
        HeaderLayout.addWidget(self.headerLabel)
        self.header.setLayout(HeaderLayout)

        self.content = QWidget()

        Layout = QVBoxLayout()
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)
        Layout.addWidget(self.header, 0)
        Layout.addWidget(self.content, 1)
        self.setLayout(Layout)

        self.headerButton.clicked.connect(self.toggle)

    def paintEvent(self, e):
        e.accept()
        p = QPainter(self)
        p.setBrush(QBrush(self.image))
        p.setPen(QColor('#b6b6b6'))
        rect = self.rect()
        rect.setWidth(rect.width()-1)
        rect.setHeight(rect.height()-1)
        p.drawRoundedRect(rect, 5, 5)

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
    if c is None:
        clearBackgroundColor(w)
    if not hasattr(w, '_orig_palette'):
        w._orig_palette = w.palette()
    p = QPalette(w.palette())
    p.setColor(QPalette.Background, c);
    w.setAutoFillBackground(True)
    w.setPalette(p)


def clearBackgroundColor(w):
    if not hasattr(w, '_orig_palette'):
        return
    w.setPalette(w._orig_palette)
    del w._orig_palette
    w.setAutoFillBackground(False)



class EmptyTabBar(QTabBar):
    def __init__(self, parent=None):
        QTabBar.__init__(self, parent)

    def paintEvent(self, e):
        pass



class Led(QFrame):
    def __init__(self, parent=None):
        QFrame.__init__(self, parent)
        h = self.fontMetrics().height()
        self.setMinimumSize(h * 2, h)
        self._color = red
        self.timer = QTimer(self)
        self.timer.setSingleShot(True)
        self.timer.timeout.connect(self.off)
        self.isOn = False
#        self.setFrameStyle(QFrame.Box)

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



""" decorator to block recursive signal emissions. """
def blocked(x):
    if type(x) == type(blocked): # function
        def wrapper(*args):
            self = args[0]
            if self.block:
                return
            was = self.block
            self.block = True
            ret = x(*args)
            self.block = was
        return wrapper
    elif isinstance(x, type):
        def init_wrapper(*args, **kwargs):
            args[0].block = False
            return x.__orig_init__(*args, **kwargs)
        x.__orig_init__ = x.__init__
        x.__init__ = init_wrapper
        return x
    else:
        assert '@blocked: not sure what to do with this: ' + str(x)


class ClickFilter(QObject):

    clicked = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        parent.installEventFilter(self)

    def eventFilter(self, o, e):
        if o == self.parent():
            if e.type() == QEvent.MouseButtonRelease:
                self.clicked.emit()
                return True
        return super().eventFilter(o, e)


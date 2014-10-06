#!/usr/bin/env python3

import os, sys
import rtmidi
import module_locator

#if module_locator.we_are_frozen():
#    print("frozen")
#    DIRNAME = os.path.dirname(os.path.realpath(sys.argv[0]))
#    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(DIRNAME, 'platforms')
#    print("QT_QPA_PLATFORM_PLUGIN_PATH = " +  os.path.join(DIRNAME, 'platforms'))
#else:
#    print("not frozen")

from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from binding import Binding



def msg2str(midi):
    s = '<rtmidi.MidiMessage>'
    if midi.isNoteOn():
        s = 'NOTE ON: (%s) %s, %s' % (midi.getChannel(), midi.getMidiNoteName(midi.getNoteNumber()), midi.getVelocity())
    elif midi.isNoteOff():
        s = 'NOTE OFF: (%s) %s' % (midi.getChannel(), midi.getMidiNoteName(midi.getNoteNumber()))
    elif midi.isController():
        s = 'CONTROLLER (%s) %s, %s' % (midi.getChannel(), midi.getControllerNumber(), midi.getControllerValue())
    return s


#_settings = QSettings('settings', QSettings.NativeFormat)
_settings = QSettings('vedanamedia', 'PKMidiStroke')

class PKMidiStroke(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.settings = _settings

        self.resize(600, 200)
        device = rtmidi.RtMidiIn()
        self.portBox = QComboBox(self)
        portName = self.settings.value('portName', type=str)
        iPort = None
        for i in range(device.getPortCount()):
            name = device.getPortName(i)
            self.portBox.addItem(name)
            if name == portName:
                iPort = i
        self.portBox.activated[int].connect(self.setInterfaceName)
        self.collector = Collector(self)
        self.collector.midi.connect(self.onMidi)
        if not iPort is None:
            self.setInterfaceName(iPort)
        self.activityLabel = QTextEdit(self)

        self.bindingsBox = QWidget(self)

        self.bindings = []
        self.addButton = QPushButton("+", self)
        self.addButton.setMaximumSize(50, 50)
        self.addButton.clicked.connect(self.addBinding)

        layout = QVBoxLayout()
        layout.addWidget(self.portBox)
        #
        BindingsLayout = QVBoxLayout()
        BindingsLayout.setContentsMargins(0, 11, 0, 11)
        self.bindingsBox.setLayout(BindingsLayout)
        layout.addWidget(self.bindingsBox)
        #
        layout.addWidget(self.activityLabel)
        self.setLayout(layout)
        #
        AddLayout = QHBoxLayout()
        AddLayout.addWidget(self.addButton)
        AddLayout.addItem(QSpacerItem(10, 10, QSizePolicy.Maximum, QSizePolicy.Maximum))
        layout.addLayout(AddLayout)
        
        self.readSettings(self.settings)

    def __del__(self):
        self.writeSettings(self.settings)

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

    def writeSettings(self, settings=None):
        if settings is None:
            settings = self.settings
        settings.setValue('size', self.size())
#        settings.setValue('width', self.width())
#        settings.setValue('height', self.height())
        settings.remove('bindings')
        settings.beginGroup('bindings')
        for i, b in enumerate(self.bindings):
            settings.beginGroup(str(i))
            b.writeSettings(settings)
            settings.endGroup()
        settings.endGroup()
        settings.sync()
    
    def setInterfaceName(self, iPort):
        device = rtmidi.RtMidiIn()
        self.portBox.setCurrentIndex(iPort)
        self.settings.setValue('portName', device.getPortName(iPort))
        device.openPort(iPort)
        self.collector.setDevice(device)
    
    def addBinding(self, save=True):
        b = Binding(self.bindingsBox)
        self.bindingsBox.layout().addWidget(b)
        b.changed.connect(self.writeSettings)
        self.layout().addWidget(b)
        self.bindings.append(b)
        self.settings.beginGroup('bindings/%s' % (len(self.bindings) - 1))
        b.writeSettings(self.settings)
        self.settings.endGroup()
        b.removeMe.connect(self.removeBinding)
        if save:
            self.settings.sync()
        return b
        
    def removeBinding(self, b):
        self.bindingsBox.layout().removeWidget(b)
        b.setParent(None)
        self.bindings.remove(b)

    def onMidi(self, midi):
        s = midi.__str__().replace('<', '').replace('>', '')
        self.activityLabel.append(s)
        for b in self.bindings:
            b.match(midi)


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
                if msg:
                    self.midi.emit(msg)



def main():
    app = QApplication(sys.argv)
    w = PKMidiStroke()
    w.show()
    app.exec()
main()

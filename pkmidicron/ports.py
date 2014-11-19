import rtmidi
from .pyqt_shim import QObject, pyqtSignal, QTimer, QCoreApplication


import time
class PortList(QObject):

    portAdded = pyqtSignal(str)
    portRemoved = pyqtSignal(str)

    def __init__(self, parent, prefs):
        super().__init__(parent)
        self.ports = {}
        self.virtualPorts = {}
        self.prefs = prefs
        self.dev = rtmidi.RtMidiIn()
        if prefs:
            prefs.beginGroup('InputPorts')
            for name in prefs.childGroups():
                prefs.beginGroup(name)
                if prefs.value('isVirtual', type=bool):
                    self.addVirtualPort(name)
                prefs.endGroup()
            prefs.endGroup()
        self.update()
        # periodically check for new names
        self.startTimer(500)

    def timerEvent(self, e):
        self.update()

    def _getPortIndex(self, name):
        return self.allPorts().index(name)

    def update(self):
        newNames = self.allPorts()
        added = set(newNames) - set(self.ports.keys())
        removed = set(self.ports.keys()) - set(newNames)
        for name in added:
            self.ports[name] = rtmidi.RtMidiIn()
            self.ports[name].openPort(self._getPortIndex(name))
            self.portAdded.emit(name)
        for name in removed:
            self.ports[name].closePort()
            del self.ports[name]
            self.portRemoved.emit(name)

    def allPorts(self):
        return [self.dev.getPortName(i) for i in range(self.dev.getPortCount())]

    def addVirtualPort(self, name):
        if name in self.virtualPorts:
            return
        dev = rtmidi.RtMidiOut()
        dev.openVirtualPort(name)
        self.virtualPorts[name] = dev
        QTimer.singleShot(0, self.update)
        self.prefs.beginGroup('InputPorts/' + name)
        self.prefs.setValue('isVirtual', True)
        self.prefs.endGroup()

    def removeVirtualPort(self, name):
        if not name in self.virtualPorts:
            return
        dev = self.virtualPorts[name]
        dev.closePort()
        del self.virtualPorts[name]
        QTimer.singleShot(0, self.update)
        self.prefs.remove('InputPorts/' + name)

    def renameVirtualPort(self, oldName, newName):
        if not oldName in self.virtualPorts:
            return
        self.removeVirtualPort(oldName)
        self.addVirtualPort(newName)

    def sendMessage(self, portName, m):
        if not portName in self.ports:
            raise ValueError('No midi output port with the name ' + portName)
        self.ports[portName].sendMessage(m)


_portList = None
def ports(parent=None, prefs=None):
    global _portList
    if _portList is None:
        if parent is None:
            parent = QCoreApplication.instance()
        _portList = PortList(parent, prefs)
    return _portList

inputs = outputs = ports

def cleanup():
    global _portList
    _portList = None

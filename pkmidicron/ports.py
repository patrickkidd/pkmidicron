import rtmidi
from .pyqt_shim import QObject, pyqtSignal, QTimer, QCoreApplication


import time
class PortList(QObject):

    portAdded = pyqtSignal(str)
    portRemoved = pyqtSignal(str)

    def __init__(self, parent, prefs):
        super().__init__(parent)
        self.names = []
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
        # periodically check for new names
        self.startTimer(500)

    def timerEvent(self, e=None):
        newNames = self.allPorts()
        added = set(newNames) - set(self.names)
        removed = set(self.names) - set(newNames)
        self.names = newNames
        for name in added:
            self.portAdded.emit(name)
        for name in removed:
            self.portRemoved.emit(name)

    def allPorts(self):
        return [self.dev.getPortName(i) for i in range(self.dev.getPortCount())]

    def addVirtualPort(self, name):
        if name in self.virtualPorts:
            return
        dev = rtmidi.RtMidiOut()
        dev.openVirtualPort(name)
        self.virtualPorts[name] = dev
        QTimer.singleShot(0, self.timerEvent)
        self.prefs.beginGroup('InputPorts/' + name)
        self.prefs.setValue('isVirtual', True)
        self.prefs.endGroup()

    def removeVirtualPort(self, name):
        if not name in self.virtualPorts:
            return
        dev = self.virtualPorts[name]
        dev.closePort()
        del self.virtualPorts[name]
        QTimer.singleShot(0, self.timerEvent)
        self.prefs.remove('InputPorts/' + name)

    def renameVirtualPort(self, oldName, newName):
        if not oldName in self.virtualPorts:
            return
        self.removeVirtualPort(oldName)
        self.addVirtualPort(newName)


_portList = None
def ports(parent=None, prefs=None):
    global _portList
    if _portList is None:
        if parent is None:
            parent = QCoreApplication.instance()
        _portList = PortList(parent, prefs)
    return _portList

def cleanup():
    global _portList
    _portList = None

import rtmidi
from .pyqt_shim import QObject, pyqtSignal, QTimer, QCoreApplication


import time
class PortList(QObject):
    """ Maintains a list of ports. This class does NOT open and close ports. """

    portAdded = pyqtSignal(str)
    portRemoved = pyqtSignal(str)

    def __init__(self, parent, prefs, input):
        super().__init__(parent)
        self.ports = {}
        self.virtualPorts = {}
        self._names_cached = []
        self.prefs = prefs
        self.isInput = bool(input)
        self.ctor = self.isInput and rtmidi.RtMidiIn or rtmidi.RtMidiOut
        self.dev = self.ctor()
        if prefs:
            if self.isInput:
                prefs.beginGroup('InputPorts')
            else:
                prefs.beginGroup('OutputPorts')
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
        return self.names().index(name)

    def update(self):
        newNames = self.names()
        added = set(newNames) - set(self.ports.keys())
        removed = set(self.ports.keys()) - set(newNames)
        for name in added:
            self.ports[name] = self.ctor()
            # print("OPEN %i: %s" % (self._getPortIndex(name), name))
            # try:
            #     self.ports[name].openPort(self._getPortIndex(name))
            # except rtmidi.Error:
            #     import traceback
            #     traceback.print_exc()
            self.portAdded.emit(name)
        for name in removed:
            self.ports[name].closePort()
            del self.ports[name]
            self.portRemoved.emit(name)

    def names(self):
        self._names_cached = [self.dev.getPortName(i) for i in range(self.dev.getPortCount())]
        return self._names_cached

    def names_cached(self):
        return self._names_cached

    def addVirtualPort(self, name):
        if name in self.virtualPorts:
            return
        dev = self.ctor()
        dev.openVirtualPort(name)
        self.virtualPorts[name] = dev
        QTimer.singleShot(0, self.update)
        if self.isInput:
            self.prefs.beginGroup('InputPorts/' + name)
        else:
            self.prefs.beginGroup('OutputPorts/' + name)
        self.prefs.setValue('isVirtual', True)
        self.prefs.endGroup()

    def removeVirtualPort(self, name):
        if not name in self.virtualPorts:
            return
        dev = self.virtualPorts[name]
        dev.closePort()
        del self.virtualPorts[name]
        QTimer.singleShot(0, self.update)
        if self.isInput:
            self.prefs.remove('InputPorts/' + name)
        else:
            self.prefs.remove('OutputPorts/' + name)

    def renameVirtualPort(self, oldName, newName):
        if not oldName in self.virtualPorts:
            return
        self.removeVirtualPort(oldName)
        self.addVirtualPort(newName)


class InputPorts(PortList):
    def __init__(self, parent, prefs):
        super().__init__(parent, prefs, True)


class OutputPorts(PortList):
    def __init__(self, parent, prefs):
        super().__init__(parent, prefs, False)

    def sendMessage(self, portName, m):
        if not portName in self.ports:
            raise ValueError('No midi output port with the name \"%s\"' % portName)
        port = self.ports[portName]
        if not port.isPortOpen():
            for i in range(port.getPortCount()):
                if port.getPortName(i) == portName:
                    port.openPort(i)
        self.ports[portName].sendMessage(m)


_outputs = None
def outputs(parent=None, prefs=None):
    global _outputs
    if _outputs is None:
        if parent is None:
            parent = QCoreApplication.instance()
        _outputs = OutputPorts(parent, prefs)
    return _outputs

_inputs = None
def inputs(parent=None, prefs=None):
    global _inputs
    if _inputs is None:
        if parent is None:
            parent = QCoreApplication.instance()
        _inputs = InputPorts(parent, prefs)
    return _inputs
    


def cleanup():
    global _inputs, _outputs
    _inputs = None
    _outputs = None

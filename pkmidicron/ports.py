import rtmidi
from .pyqt_shim import QObject, pyqtSignal, QTimer, QCoreApplication, QApplication, QThread, QMutex


import socket, struct, time
class Network(QThread):
    """The engine for sending midi over network.  We basically just send
    over UDP multicast, and a periodic ping keeps the list of hosts
    alive. Super simple.
    """
    PORT = 8123
    GROUP = '225.0.0.250'
    TTL = 1 # Increase to reach other networks

    _self = None

    hostAdded = pyqtSignal(str)
    hostRemoved = pyqtSignal(str)

    def __init__(self, parent, prefs):
        super().__init__(parent)
        if Network._self:
            raise ValueError('only one instance of Network class allowed')
        Network._self = self

        # Look up multicast group address in name server and find out IP version
        self.addrinfo = socket.getaddrinfo(self.GROUP, None)[0]
        self.ssock = None
        self.rsock = None
        self.hostname = socket.gethostname()
        self.prefs = prefs
        self.hosts = {}
        self._running = False
        self.timer = None
        self.mutex = QMutex()
        self.startTimer(1000)

    @staticmethod
    def instance(prefs=None):
        if not Network._self:
            Network._self = Network(QCoreApplication.instance(), prefs)
        return Network._self
        
    def timerEvent(self, e):
        """ 
        - Periodically send ping to alert hosts of existance.
        - Expire old hosts who haven't pinged in a while.
        """
        if not self.ssock:
            self.ssock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
            # Set Time-to-live (optional)
            ttl_bin = struct.pack('@i', self.TTL)
            self.ssock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl_bin)
        ping_data = 'pkmidicron:ping:' + self.hostname
        self.ssock.sendto(ping_data.encode('utf-8'), (self.addrinfo[4][0], self.PORT))
        # check for stale hosts
        died = []
        self.mutex.lock()
        for name, host in self.hosts.items():
            if time.time() - host['ping'] > 3:
                died.append(name)
        for name in died:
            del self.hosts[name]
            self.hostRemoved.emit(name)
        if len(died) > 0:
            outputs().update()
            inputs().update()
        self.mutex.unlock()

    def run(self):
        """ listen for packets, maintain host list. """
        if self.rsock:
            raise ValueError('recieve socket already running')
        self.rsock = socket.socket(self.addrinfo[0], socket.SOCK_DGRAM)
        # Allow multiple copies of this program on one machine (not strictly needed)
        self.rsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.rsock.bind(('', self.PORT))
        group_bin = socket.inet_pton(self.addrinfo[0], self.addrinfo[4][0])
        # Join group
        mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
        self.rsock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        self.rsock.setblocking(False)
        self.rsock.settimeout(.5)
        while self._running:
            try:
                data, sender = self.rsock.recvfrom(1024)
            except socket.timeout:
                continue
            while data[-1:] == '\0': data = data[:-1] # Strip trailing \0's
            try:
                sdata = data.decode('utf-8')
            except UnicodeDecodeError:
                sdata = None
            hostname = None
            if sdata and sdata.startswith('pkmidicron:ping:'): # host ping
                hostname = sdata.replace('pkmidicron:ping:', '').split('\0',1)[0] # remove '\0'
                added = False
                if self.hostname != hostname:
                    self.mutex.lock()
                    if not hostname in self.hosts:
                        # print('host up:', hostname, sender)
                        self.hosts[hostname] = {
                            'ping': time.time(),
                            'ip': sender[0],
                            'port': sender[1],
                            'name': hostname
                        }
                        added = True
                    else:
                        self.hosts[hostname]['ping'] = time.time()
                    self.mutex.unlock()
                if added:
                    self.hostAdded.emit(hostname)
            else: # recv midi message
                info = self.isHostUp(sender)
                if info:
                    w = QApplication.instance().getMainWindow()
                    if w:
                        name = info['name']
                        enabled = self.prefs.value('InputPorts/' + name + '/enabled', type=bool, defaultValue=True)
                        if w.enableAllInputs or enabled:
                            msg = rtmidi.MidiMessage(data)
                            if w.collector: # lots of msgs coming in before mainwindow is initialized
                                w.collector.postMessage(name, msg)
        self.rsock.close()
        self.rsock = None

    def start(self):
        if self._running:
            return
        self._running = True
        super().start()
        self.timer = self.startTimer(1000)

    def stop(self):
        if not self._running:
            return
        self._running = False
        self.wait()
        if self.ssock:
            self.ssock.close()
            self.ssock = None
        # clear the ports list
        for name, info in self.hosts.items():
            self.hostRemoved.emit(name)
        self.hosts = {}
        self.killTimer(self.timer)
        self.timer = None
        
    def isHostUp(self, sender):
        for hostname, info in self.hosts.items():
            if sender[1] == info['port']: # not sure why I can't check IP too from parallels...
                return info
        return False

    def isEnabled(self):
        return self._running

    def portNames(self):
        return list(self.hosts)

    def sendMessage(self, name, msg):
        """ just send to the whole group and let them filter on the recieving side. """
        self.ssock.sendto(msg.getRawData(), (self.addrinfo[4][0], self.PORT))
        

class NetworkPort:
    """ Network stand-in for RtMidi dev """
    def __init__(self, name):
        self.name = name

    def isPortOpen(self):
        """ Dummy """
        return True

    def closePort(self):
        """ dummy """
        pass

    def sendMessage(self, m):
        Network.instance().sendMessage(self.name, m)
        

import time
class PortList(QObject):
    """ Maintains a list of ports. This class does NOT open and close ports. """

    portAdded = pyqtSignal(str)
    portRemoved = pyqtSignal(str)

    def __init__(self, parent, prefs, input):
        super().__init__(parent)
        self.ports = {}
        self.virtualPorts = {}
        self.networkPorts = {}
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
        networkNames = Network.instance().portNames()
        for name in added:
            if name in networkNames + ['Network Bus']:
                self.ports[name] = NetworkPort(name)
            else:
                self.ports[name] = self.ctor()
            self.portAdded.emit(name)
        for name in removed:
            self.ports[name].closePort()
            del self.ports[name]
            self.portRemoved.emit(name)

    def names(self):
        self._names_cached = [self.dev.getPortName(i) for i in range(self.dev.getPortCount())]
        if self.isInput:
            self._names_cached = self._names_cached + Network.instance().portNames()
        else:
            if Network.instance().isEnabled():
                self._names_cached.append("Network Bus")
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
        Network.instance().hostAdded.connect(self.update)
        Network.instance().hostRemoved.connect(self.update)

class OutputPorts(PortList):
    def __init__(self, parent, prefs):
        super().__init__(parent, prefs, False)
        Network.instance().hostAdded.connect(self.update)
        Network.instance().hostRemoved.connect(self.update)

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
    Network.instance().stop()
    Network._self = None


    

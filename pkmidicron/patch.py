import os
import rtmidi
from . import util
from .pyqt_shim import QSettings, QObject, pyqtSignal, QFileInfo


class MidiMessage(QObject):

    changed = pyqtSignal()

    WILDCARD = -1
    
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.portName = None
        self.midi = rtmidi.MidiMessage.noteOn(1, 0, 100)
        self.wildcards = {
            "channel": False,
            "noteNum": False,
            "noteVel": False,
            "ccNum": False,
            "ccValue": False,
            "atNum": False,
            "atValue": False,
        }

    def read(self, patch):
        self.portName = patch.value('portName', type=str)
        iType = patch.value('type', type=int)
        channel = patch.value('channel', type=int)
        if iType == util.MSG_NOTE_ON:
            self.midi = rtmidi.MidiMessage.noteOn(channel,
                                                  patch.value('noteNum', type=int),
                                                  patch.value('noteVel', type=int))
        elif iType == util.MSG_NOTE_OFF:
            self.midi = rtmidi.MidiMessage.noteOff(channel,
                                                   patch.value('noteNum', type=int))
        elif iType == util.MSG_CC:
            self.midi = rtmidi.MidiMessage.controllerEvent(channel,
                                                           patch.value('ccNum', type=int),
                                                           patch.value('ccValue', type=int))
        elif iType == util.MSG_AFTERTOUCH:
            self.midi = rtmidi.MidiMessage.aftertouchChange(channel,
                                                            patch.value('atNum', type=int),
                                                            patch.value('atValue', type=int))
        patch.beginGroup('wildcards')
        for key in self.wildcards.keys():
            self.wildcards[key] = patch.value(key, type=bool)
        patch.endGroup()

    def write(self, patch):
        if self.portName is not None:
            patch.setValue('portName', self.portName)
        patch.setValue('channel', self.midi.getChannel())
        if self.midi.isNoteOn():
            patch.setValue('type', util.MSG_NOTE_ON)
            patch.setValue('noteNum', self.midi.getNoteNumber())
            patch.setValue('noteVel', self.midi.getVelocity())
        elif self.midi.isNoteOff():
            patch.setValue('type', util.MSG_NOTE_OFF)
            patch.setValue('noteNum', self.midi.getNoteNumber())
        elif self.midi.isController():
            patch.setValue('type', util.MSG_CC)
            patch.setValue('ccNum', self.midi.getControllerNumber())
            patch.setValue('ccValue', self.midi.getControllerValue())
        elif self.midi.isAftertouch():
            patch.setValue('type', util.MSG_AFTERTOUCH)
            patch.setValue('atNum', self.midi.getNoteNumber())
            patch.setValue('atValue', self.midi.getAfterTouchValue())
        patch.beginGroup('wildcards')
        for key, value in self.wildcards.items():
            patch.setValue(key, value)
        patch.endGroup()

    def setMidi(self, portName, midi):
        self.portName = portName
        self.midi = midi
        self.changed.emit()

    def setWildcard(self, key, x, emit=True):
        if not key in self.wildcards:
            raise KeyError('%s is not a valid MidiMessage value' % key)
        self.wildcards[key] = x
        if emit:
            self.changed.emit()
 

class Simulator(MidiMessage):
    def __init__(self, parent=None):
        MidiMessage.__init__(self, parent)


class Criteria(MidiMessage):

    def __init__(self, parent=None):
        MidiMessage.__init__(self, parent)

    def match(self, portName, midi):
        if portName != self.portName and self.portName != util.ANY_TEXT:
            return

        m1 = rtmidi.MidiMessage(midi)
        m2 = rtmidi.MidiMessage(self.midi)

        if m2.isNoteOn() or m2.isNoteOff():
            if self.wildcards['channel']:
                if m2.getVelocity() > 0: # careful!
                    m2 = rtmidi.MidiMessage.noteOn(m1.getChannel(),
                                                   m2.getNoteNumber(),
                                                   m2.getVelocity())
                else:
                    m2 = rtmidi.MidiMessage.noteOff(m1.getChannel(),
                                                    m2.getNoteNumber())
            if self.wildcards['noteNum']:
                m2.setNoteNumber(m1.getNoteNumber())
            if self.wildcards['noteVel'] and m1.getVelocity() > 0: # careful!
                m2.setVelocity(m1.getVelocity() / 127.0)
        elif m2.isController():
            if self.wildcards['ccNum']:
                m2 = rtmidi.MidiMessage.controllerEvent(m2.getChannel(),
                                                        m1.getControllerNumber(),
                                                        m2.getControllerValue())
            if self.wildcards['ccValue']:
                m2 = rtmidi.MidiMessage.controllerEvent(m2.getChannel(),
                                                        m2.getControllerNumber(),
                                                        m1.getControllerValue())
            if self.wildcards['channel']:
                m2 = rtmidi.MidiMessage.controllerEvent(m1.getChannel(),
                                                        m2.getControllerNumber(),
                                                        m2.getControllerValue())
        elif m2.isAftertouch():
            if self.wildcards['atNum']:
                m2 = rtmidi.MidiMessage.aftertouchChange(m2.getChannel(),
                                                         m1.getNoteNumber(),
                                                         m2.getAfterTouchValue())
            if self.wildcards['atValue']:
                m2 = rtmidi.MidiMessage.aftertouchChange(m2.getChannel(),
                                                         m2.getNoteNumber(),
                                                         m1.getAfterTouchValue())
            if self.wildcards['channel']:
                m2 = rtmidi.MidiMessage.aftertouchChange(m1.getChannel(),
                                                         m2.getNoteNumber(),
                                                         m2.getAfterTouchValue())
        return m1 == m2


class Action(QObject):
    
    changed = pyqtSignal()

    def __init__(self, iType, parent=None):
        QObject.__init__(self, parent)
        self.type = iType

    def read(self, patch):
        self.type = patch.value('type', type=int)

    def write(self, patch):
        patch.setValue('type', self.type)

    def trigger(self, midi):
        pass

    def getPatch(self):
        return self.parent().getPatch()


class SendMessageAction(Action):
    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_SEND_MESSAGE, parent)
        self.midiMessage = MidiMessage(self)
        self.midiMessage.changed.connect(self.onMidiChanged)
        self.forward = False
        self.device = None

    def read(self, patch):
        super().read(patch)
        self.forward = patch.value('forward', type=bool)
        patch.beginGroup('MidiMessage')
        self.midiMessage.read(patch)
        patch.endGroup()

    def write(self, patch):
        super().write(patch)
        patch.setValue('forward', self.forward)
        patch.beginGroup('MidiMessage')
        self.midiMessage.write(patch)
        patch.endGroup()

    def trigger(self, midi):
        if not self.device:
            self.device = util.openPort(self.midiMessage.portName)
            if not self.device:
                return
        was = self.getPatch().setBlock(True)
        if self.forward:
            self.device.sendMessage(midi)
        else:
            self.device.sendMessage(self.midiMessage.midi)
        self.getPatch().setBlock(was)

    def setForward(self, x):
        self.forward = bool(x)
        self.changed.emit()

    def onMidiChanged(self):
        self.changed.emit()
        self.device = util.openPort(self.midiMessage.portName)


class OpenFileAction(Action):
    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_OPEN_FILE, parent)
        self.text = None

    def read(self, patch):
        super().read(patch)
        self.text = patch.value('text', type=str)

    def write(self, patch):
        super().write(patch)
        patch.setValue('text', self.text)

    def setText(self, x):
        self.text = x
        self.changed.emit()


class RunProgramAction(Action):
    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_RUN_PROGRAM, parent)
        self.text = None

    def read(self, patch):
        super().read(patch)
        self.text = patch.value('text', type=str)

    def write(self, patch):
        super().write(patch)
        patch.setValue('text', self.text)

    def setText(self, x):
        self.text = x
        self.changed.emit()

    def trigger(self, midi):
        if self.text:
            os.system(self.text)


class Binding(QObject):

    changed = pyqtSignal()
    triggered = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.criteria = [
            Criteria(self)
        ]
        self.criteria[0].changed.connect(self.changed.emit)
        self.actions = []
        self.title = ''
        self.triggerCount = 0
        self.enabled = True

    def getPatch(self):
        return self.parent()

    def clear(self):
        for c in self.criteria:
            c.setParent(None)
        self.criteria = []
        for a in self.actions:
            a.setParent(None)
        self.actions = []

    def read(self, patch):
        self.clear()
        self.title = patch.value('title', type=str)
        self.enabled = patch.value('enabled', type=bool)
        patch.beginGroup('criteria')
        for i in patch.childGroups():
            patch.beginGroup(i)
            criteria = self.addCriteria()
            criteria.read(patch)
            patch.endGroup()
        patch.endGroup()
        if not self.criteria:
            self.criteria = [
                Criteria(self)
            ]
        patch.beginGroup('actions')
        for i in patch.childGroups():
            patch.beginGroup(str(i))
            iType = patch.value('type', type=int)
            action = self.addAction(iType)
            action.read(patch)
            patch.endGroup()
        patch.endGroup()

    def write(self, patch): 
        patch.setValue('title', self.title)
        patch.setValue('enabled', self.enabled)
        patch.remove('criteria')
        patch.beginGroup('criteria')
        for i, criteria in enumerate(self.criteria):
            patch.beginGroup(str(i))
            criteria.write(patch)
            patch.endGroup()
        patch.endGroup()
        patch.remove('actions')
        patch.beginGroup('actions')
        for i, action in enumerate(self.actions):
            patch.beginGroup(str(i))
            action.write(patch)
            patch.endGroup()
        patch.endGroup()

    #

    def setTitle(self, x):
        self.title = x
        self.changed.emit()

    def setEnabled(self, x):
        self.enabled = bool(x)

    def addCriteria(self):
        criteria = Criteria(self)
        criteria.changed.connect(self.changed.emit)
        self.criteria.append(criteria)
        return criteria

    def addAction(self, iType):
        if iType == util.ACTION_SEND_MESSAGE:
            action = SendMessageAction(self)
        elif iType == util.ACTION_RUN_PROGRAM:
            action = RunProgramAction(self)
        elif iType == util.ACTION_OPEN_FILE:
            action = OpenFileAction(self)
        else:
            raise ValueError('unknown action type')
        action.changed.connect(self.changed.emit)
        self.actions.append(action)
        return action

    def removeAction(self, action):
        self.actions.remove(action)

    def onMidiMessage(self, portName, midi):
        found = False
        for c in self.criteria:
            if c.match(portName, midi):
                found = True
                break
        if not found:
            return
        self.onMatched(midi)

    def onMatched(self, midi):
        self.triggerCount += 1
        self.triggered.emit()
        for action in self.actions:
            action.trigger(midi)


class Patch(QObject):

    dirtyChanged = pyqtSignal(bool)

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.bindings = []
        self.simulator = Simulator(self)
        self.simulator.changed.connect(self.setDirty)
        self.dirty = False
        self.block = False
        self.fileName = 'Untitled.pmc'
        self.filePath = 'Untitled.pmc'

    def read(self, filePath):
        patch = util.Settings(filePath, QSettings.IniFormat)
        patch.beginGroup('bindings')
        for i in patch.childGroups():
            patch.beginGroup(i)
            binding = Binding(self)
            binding.read(patch)
            binding.changed.connect(self.setDirty)
            self.bindings.append(binding)
            patch.endGroup()
        patch.endGroup()
        patch.beginGroup('simulator')
        self.simulator.read(patch)
        patch.endGroup()
        self.filePath = QFileInfo(filePath).filePath()
        self.fileName = QFileInfo(filePath).fileName()

    def write(self, filePath):
        patch = util.Settings(filePath, QSettings.IniFormat)
        patch.remove('bindings')
        patch.beginGroup('bindings')
        for i, binding in enumerate(self.bindings):
            patch.beginGroup(str(i))
            binding.write(patch)
            patch.endGroup()
        patch.endGroup()
        patch.remove('simulator')
        patch.beginGroup('simulator')
        self.simulator.write(patch)
        patch.endGroup()
        patch.sync()
        self.filePath = QFileInfo(filePath).filePath()
        self.fileName = QFileInfo(filePath).fileName()

    def setDirty(self, x=True):
        if type(x) != bool:
            x = True
        if x != self.dirty:
            self.dirty = x
            self.dirtyChanged.emit(x)

    def addBinding(self, binding=None):
        if binding is None:
            binding = Binding(self)
        binding.changed.connect(self.setDirty)
        title = 'Binding %i' % (len(self.bindings) + 1)
        binding.title = title
        self.bindings.append(binding)
        self.setDirty(True)
        return binding

    def removeBinding(self, binding):
        self.bindings.remove(binding)
        binding.setParent(None)
        self.setDirty(True)

    def onMidiMessage(self, portName, midi):
        for b in self.bindings:
            if b.enabled:
                b.onMidiMessage(portName, midi)

    def setBlock(self, x):
        y = self.block
        self.block = bool(x)
        return y

import os
import io
import types
import sys
import time
import rtmidi
import slugify
from .util import refs
from . import util, ports, scripteditor
from .pyqt_shim import Qt, QSettings, QObject, pyqtSignal, QFileInfo, QSize


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
        self.portName = util.ALL_TEXT


class Criteria(MidiMessage):

    def __init__(self, parent=None):
        MidiMessage.__init__(self, parent)
        self.portName = util.ANY_TEXT

    def clear(self):
        pass

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

    def clear(self):
        pass

    def read(self, patch):
        self.type = patch.value('type', type=int)

    def write(self, patch):
        patch.setValue('type', self.type)

    def trigger(self, midi):
        pass

    def getPatch(self):
        return self.parent().getPatch()

    def testScript(self):
        midi = rtmidi.MidiMessage.noteOn(1, 100, 100)
        self.trigger(midi)


class SendMessageAction(Action):
    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_SEND_MESSAGE, parent)
        self.midiMessage = MidiMessage(self)
        self.midiMessage.changed.connect(self.onMidiChanged)
        self.forward = False

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
        if not self.portName:
            return
        was = self.getPatch().setBlock(True)
        if self.forward:
            ports.outputs().sendMessage(self.midiMessage.portName, midi)
        else:
            ports.outputs().sendMessage(self.midiMessage.portName, self.midiMessage.midi)
        self.getPatch().setBlock(was)

    def setForward(self, x):
        self.forward = bool(x)
        self.changed.emit()

    def onMidiChanged(self):
        self.changed.emit()


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

    def trigger(self, midi):
        if self.text:
            os.system('open ' + self.text)


class RunProgramAction(Action):
    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_RUN_PROGRAM, parent)
        self.text = None

#    def __del__(self):
#        print('RunProgramAction.__del__')

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
            if self.text.endswith('.app'):
                os.system('open ' + self.text)
            else:
                os.system(self.text)



class RunScriptAction(Action):

    lastIndex = 1

    def __init__(self, parent=None):
        Action.__init__(self, util.ACTION_RUN_SCRIPT, parent)
        self.source = None
        self.editor = None # bleh
        self.editorSizes = None
        self.editorSplitterSizes = None
        self.module = None
        self.name = 'RunScriptAction_%i' % RunScriptAction.lastIndex
        self.slug = self.getSlug(self.name)
        self.editorSize = None
        self.editorSplitterSizes = None
        RunScriptAction.lastIndex += 1

    def clear(self):
        if self.editor:
            self.editor.close()
            self.editor = None
        if self.module:
            self.resetMod()
            self.module = None

    def read(self, patch):
        super().read(patch)
        source = patch.value('source', type=str, defaultValue=None)
        self.name = patch.value('name', type=str)
        self.slug = self.getSlug(self.name)
        if not source:
            self.source = None
        else:
            self.doSetSource(source)
        self.editorSize = patch.value('editor/size', type=QSize, defaultValue=QSize(800, 600))
        self.editorSplitterSizes = util.int_list(patch.value('editor/splitterSizes'))

    def write(self, patch):
        super().write(patch)
        patch.setValue('source', self.source)
        if self.editor:
            patch.setValue('editor/size', self.editor.size())
            patch.setValue('editor/splitterSizes', self.editor.splitter.sizes())
        patch.setValue('name', self.name)

    def resetMod(self):
        if not self.module:
            return
        # try to clear out the module by deleting all global refs
        d = self.module.__dict__
        for k in dict(d).keys():
            if not k in ['__spec__', '__name__', '__loader__',
                         '__package__', '__doc__', '__builtins__']:
                del d[k]

    def doSetSource(self, x):
        self.source = x
        if not self.module:
            self.module = types.ModuleType(self.name)
        self.resetMod()
        self.module.__dict__.update({
            'inputs': ports.inputs,
            'outputs': ports.outputs,
            'print': self.mod_print,
            '__file__': self.slug,
        })
        try:
            exec(self.source, self.module.__dict__)
            success = True
        except:
            self.printTraceback()
            success = False
        if success:
            sys.modules[self.slug] = self.module
        

    def printTraceback(self):
        if self.editor:
            import traceback
            # take out the first stack frame so you don't see app code
            lines = traceback.format_exc().splitlines()
            first = lines[0]
            diads = lines[1:-1]
            last = lines[-1]
            lines = [first] + diads[2:] + [last]
            lines = [s.replace('<string>', '<script>') for s in lines]
            self.editor.appendConsole('\n'.join(lines))

    def mod_print(self, *args, **kwargs):
        if self.editor:
            s = ' '.join([str(x) for x in args])
            self.editor.appendConsole(s)
        else:
            print(*args, **kwargs)

    def getSlug(self, x):
        return slugify.slugify(x).replace('-', '_')

    def setSource(self, x):
        self.doSetSource(x)
        self.getPatch().setDirty()
        self.changed.emit()

    def setName(self, x):
        if not str(x):
            return
        oldName = self.name
        self.name = str(x)
        self.slug = self.getSlug(self.name)
        if self.module:
            self.module.__name__ = self.slug
            if oldName in sys.modules:
                del sys.modules[oldName]
                sys.modules[self.name] = self.module
        self.getPatch().setDirty()
        self.changed.emit()

    def showEditor(self):
        if not self.editor:
            self.editor = scripteditor.ScriptEditor()
            self.editor.setText(self.source)
            self.editor.closed.connect(self.save)
            self.editor.saved.connect(self.save)
            self.editor.test.connect(self.testScript)
            if self.editorSize:
                self.editor.resize(self.editorSize)
            if self.editorSplitterSizes:
                self.editor.splitter.setSizes(self.editorSplitterSizes)
                self.editor.updateResize()
            else:
                self.editor.splitter.setSizes([100, 0])
        self.editor.show()
        self.editor.updateResize()
        self.editor.raise_()

    def save(self):
        #if self.editor.dirty:
        text = self.editor.text()
        self.setSource(text)
        self.editor.setDirty(False)

    def trigger(self, midi):
        if hasattr(self.module, 'onMidiMessage'):
            try:
                self.module.onMidiMessage(midi)
            except:
                self.printTraceback()


class Binding(QObject):

    changed = pyqtSignal()
    triggered = pyqtSignal()

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.criteria = [
            Criteria(self)
        ]
#        self.criteria[0].changed.connect(self.changed.emit)
        self.actions = []
        self.title = ''
        self.triggerCount = 0
        self.enabled = True

#    def __del__(self):
#       print('Binding.__del__')

    def getPatch(self):
        return self.parent()

    def clear(self):
        for c in self.criteria:
            c.clear()
            c.setParent(None)
        self.criteria = []
        for a in self.actions:
            a.clear()
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
        elif iType == util.ACTION_RUN_SCRIPT:
            action = RunScriptAction(self)
        else:
            raise ValueError('unknown action type')
        action.changed.connect(self.changed.emit)
        self.actions.append(action)
        self.getPatch().setDirty()
        return action

    def removeAction(self, action):
        self.actions.remove(action)
        action.clear()
        action.setParent(None)
        self.getPatch().setDirty()

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
        binding.clear()
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

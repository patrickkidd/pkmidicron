import os
from .pyqt_shim import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython
from . import util

if hasattr(os, 'uname'):
    font = QFont('Andale Mono')
    font.setPointSize(12)
else:
    font = QFont('Courier New')
    font.setPointSize(10)

BUTTON_WIDTH = 80

TINT_COMPILED = QColor('#dcffdb')
TINT_EDITED = QColor('#fdffbd')
TINT_ERROR = QColor('#ffdbdb')

STATE_COMPILED = 1
STATE_EDITED = 2
STATE_ERROR = 3


class Editor(QsciScintilla):

    saved = pyqtSignal()
    test = pyqtSignal()
    toggleConsole = pyqtSignal()
    shown = pyqtSignal()
    hidden = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.resize(500, 500)

        self.isCollapsed = False
        self.setProperty("canHaveFocus", True)
        self.viewport().setProperty("canHaveFocus", True)
        self.lastErrorMarker = None

        self.errorLine = self.markerDefine(QsciScintilla.Background)
#        self.setMarkerBackgroundColor(TINT_ERROR, self.errorLine)
        self.setEolMode(QsciScintilla.EolUnix)
        self.setAutoIndent(True)
        self.setMarginType(1, QsciScintilla.NumberMargin)
        self.setMarginWidth(1, 25)
        self.setMarginsBackgroundColor(TINT_COMPILED)
        self.setMarginLineNumbers(1, True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setLexer(QsciLexerPython(self))

        self.setFont(font)
        # self.lexer().setPaper(QColor('red'))

        self.compileButton = QPushButton(tr('Compile'), self)
        self.compileButton.clicked.connect(self.saved.emit)
        self.compileButton.setFixedWidth(BUTTON_WIDTH)

        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(self.test.emit)
        self.testButton.setFixedWidth(BUTTON_WIDTH)

        self.consoleButton = QPushButton(tr('Console'), self)
        self.consoleButton.clicked.connect(self.toggleConsole.emit)
        self.consoleButton.setFixedWidth(BUTTON_WIDTH)
        # self.consoleButton.hide()

        self.indentAction = QAction(tr("Indent Selection"), self)
        self.indentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketRight))
        self.indentAction.triggered.connect(self.indentLineOrSelection)
        self.addAction(self.indentAction)
        
        self.unindentAction = QAction(tr("Unindent Selection"), self)
        self.unindentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketLeft))
        self.unindentAction.triggered.connect(self.unindentLineOrSelection)
        self.addAction(self.unindentAction)

        self.saveAction = QAction(tr("Save"), self)
        self.saveAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_S))
        self.saveAction.triggered.connect(self.saved.emit)
        self.addAction(self.saveAction)

        self.resizeEvent(None)

    def resizeEvent(self, e):
        if e:
            super().resizeEvent(e)
            if self.isCollapsed and e.size().height() > 0:
                self.isCollapsed = False
                self.shown.emit()
            elif not self.isCollapsed and e.size().height() == 0:
                self.isCollapsed = True
                self.hidden.emit()            
        self.compileButton.move(self.width() - self.compileButton.width(), 0)
        self.testButton.move(self.width() - self.testButton.width(),
                             self.compileButton.height())
        self.consoleButton.move(self.width() - self.consoleButton.width(),
                                self.testButton.y() + self.testButton.height())

    def showEvent(self, e):
        super().showEvent(e)
        self.resizeEvent(None)

    def setFont(self, f):
        super().setFont(f)
        self.lexer().setFont(f)

    def indentLineOrSelection(self):
        pass

    def unindentLineOrSelection(self):
        pass

    def setExceptionLine(self, iLine):
        if self.lastErrorMarker:
            self.markerDeleteHandle(self.lastErrorMarker)
            self.lastErrorMarker = None
        if iLine is not None:
            self.lastErrorMarker = self.markerAdd(iLine - 1, self.errorLine)
            self.ensureLineVisible(iLine)
        self.update()

    def setExceptionLineColor(self, c):
        self.setMarkerBackgroundColor(c, self.errorLine)



class Console(QTextEdit):

    shown = pyqtSignal()
    hidden = pyqtSignal()
    showEditor = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.isCollapsed = False
        self.setFrameStyle(QFrame.NoFrame)
        self.setReadOnly(True)
        self.setFont(font)
#        p = QPalette(self.palette())
#        p.setColor(QPalette.Base, QColor('black'))
#        p.setColor(QPalette.Text, QColor('white'))
#        self.setPalette(p)

        self.clearButton = QPushButton(tr('Clear'), self)
        self.clearButton.clicked.connect(self.clear)
        self.clearButton.setFixedWidth(BUTTON_WIDTH)

        self.editorButton = QPushButton(tr('Editor'), self)
        self.editorButton.clicked.connect(self.showEditor)
        self.editorButton.setFixedWidth(BUTTON_WIDTH)
        self.editorButton.hide()

        self.resizeEvent(None)        

    def resizeEvent(self, e):
        if e:
            super().resizeEvent(e)
            if self.isCollapsed and e.size().height() > 0:
                self.isCollapsed = False
                self.shown.emit()
            elif not self.isCollapsed and e.size().height() == 0:
                self.isCollapsed = True
                self.hidden.emit()
        self.clearButton.move(self.width() - self.clearButton.width(), 0)
        self.editorButton.move(self.width() - self.editorButton.width(),
                               self.clearButton.height())


@util.blocked
class ScriptEditor(QWidget):

    closed = pyqtSignal()
    saved = pyqtSignal()
    textChanged = pyqtSignal()
    test = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.lastState = STATE_COMPILED

        self.editor = Editor(self)
        self.editor.saved.connect(self.saved.emit)
        self.editor.test.connect(self.test.emit)
        self.editor.toggleConsole.connect(self.toggleConsole)
        self.editor.textChanged.connect(self.onTextChanged)

        self.console = Console(self)
        self.console.showEditor.connect(self.showEditor)

        self.editor.shown.connect(self.console.editorButton.hide)
        self.editor.hidden.connect(self.console.editorButton.show)
        #self.console.shown.connect(self.editor.consoleButton.hide)
        #self.console.hidden.connect(self.editor.consoleButton.show)

        self.splitter = QSplitter(Qt.Vertical, self)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.console)

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.splitter)
        self.setLayout(Layout)

#        self.setDirtyState(STATE_COMPILED)

    def updateResize(self):
        self.editor.resizeEvent(None)
        self.console.resizeEvent(None)
        
    @util.blocked
    def setText(self, x):
        self.editor.setText(x)

    def closeEvent(self, e):
        self.closed.emit()

    @util.blocked
    def onTextChanged(self):
        self.block = False
        self.setDirtyState(STATE_EDITED)
        self.block = True
        self.textChanged.emit()

    def text(self):
        return self.editor.text()

    def toggleConsole(self):
        sizes = self.splitter.sizes()
        if sizes[1] == 0:
            self.splitter.setSizes([sizes[0] - 200, 200])
            self.console.show()
        else:
            self.splitter.setSizes([sizes[0], 0])
            self.console.hide()

    def showEditor(self):
        sizes = self.splitter.sizes()
        if sizes[0] == 0:
            self.splitter.setSizes([400, sizes[1] - 400])

    def appendConsole(self, s):
        p = QPalette(self.console.palette())
        p.setColor(QPalette.Base, QColor('red'))
        self.console.setPalette(p)
        self.console.append(s)

    @util.blocked
    def setDirtyState(self, state):
        if state == self.lastState:
            return
        if state == STATE_COMPILED:
            c = TINT_COMPILED
        elif state == STATE_EDITED:
            c = TINT_EDITED
        elif state == STATE_ERROR:
            c = TINT_ERROR
        self.editor.setExceptionLineColor(c)
#        p = QPalette(self.console.palette())
#        p.setColor(QPalette.Base, c)
#        self.console.setPalette(p)
        self.editor.setMarginsBackgroundColor(c)
        # don't know why this doesn't work
#        p = QPalette(self.editor.compileButton.palette())
#        p.setColor(QPalette.Button, c)
#        self.editor.compileButton.setPalette(p)


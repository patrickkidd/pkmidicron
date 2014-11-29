import os
from .pyqt_shim import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython



if hasattr(os, 'uname'):
    font = QFont('Andale Mono')
    font.setPointSize(12)
else:
    font = QFont('Courier New')
    font.setPointSize(10)
BUTTON_WIDTH = 80

TINT = QColor('#dcffdb')

class Editor(QsciScintilla):

    saved = pyqtSignal()
    test = pyqtSignal()
    showConsole = pyqtSignal()
    shown = pyqtSignal()
    hidden = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.isCollapsed = False
        self.setProperty("canHaveFocus", True)
        self.viewport().setProperty("canHaveFocus", True)
        self.errorLine = self.markerDefine(QsciScintilla.Background)
        self.resize(500, 500)
  
        highlightColor = QColor('yellow')
        highlightColor.setAlpha(0.3921568627451)
      
        self.setMarkerBackgroundColor(highlightColor)
        self.setEolMode(QsciScintilla.EolUnix)
        self.setAutoIndent(True)
        self.setMarginType(1, QsciScintilla.NumberMargin)
        self.setMarginWidth(1, 25)
        self.setMarginsBackgroundColor(TINT)
        self.setMarginLineNumbers(1, True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setLexer(QsciLexerPython(self))

        self.setFont(font)
        # self.lexer().setPaper(QColor('red'))

        self.textChanged.connect(self.parent().setDirty)

        self.saveButton = QPushButton(tr('Save'), self)
        self.saveButton.clicked.connect(self.saved.emit)
        self.saveButton.setFixedWidth(BUTTON_WIDTH)

        self.testButton = QPushButton(tr('Test'), self)
        self.testButton.clicked.connect(self.test.emit)
        self.testButton.setFixedWidth(BUTTON_WIDTH)

        self.consoleButton = QPushButton(tr('Console'), self)
        self.consoleButton.clicked.connect(self.showConsole.emit)
        self.consoleButton.setFixedWidth(BUTTON_WIDTH)
        self.consoleButton.hide()

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
        self.saveButton.move(self.width() - self.saveButton.width(), 0)
        self.testButton.move(self.width() - self.testButton.width(),
                             self.saveButton.height())
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


class Console(QTextEdit):

    shown = pyqtSignal()
    hidden = pyqtSignal()
    showEditor = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.isCollapsed = False
        self.setFrameStyle(QFrame.NoFrame)
        self.setReadOnly(True)
        p = QPalette(self.palette())
        p.setColor(QPalette.Base, TINT)
        p.setColor(QPalette.Text, QColor('black'))
        self.setPalette(p)
        self.setFont(font)

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



class ScriptEditor(QWidget):

    closed = pyqtSignal()
    saved = pyqtSignal()
    textChanged = pyqtSignal()
    test = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dirty = False

        self.editor = Editor(self)
        self.editor.saved.connect(self.saved.emit)
        self.editor.textChanged.connect(self.textChanged.emit)
        self.editor.test.connect(self.test.emit)
        self.editor.showConsole.connect(self.showConsole)

        self.console = Console(self)
        self.console.showEditor.connect(self.showEditor)

        self.editor.shown.connect(self.console.editorButton.hide)
        self.editor.hidden.connect(self.console.editorButton.show)
        self.console.shown.connect(self.editor.consoleButton.hide)
        self.console.hidden.connect(self.editor.consoleButton.show)

        self.splitter = QSplitter(Qt.Vertical, self)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.console)

        Layout = QVBoxLayout(self)
        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.addWidget(self.splitter)
        self.setLayout(Layout)

    def updateResize(self):
        self.editor.resizeEvent(None)
        self.console.resizeEvent(None)
        
    def setText(self, x):
        self.editor.setText(x)

    def closeEvent(self, e):
        self.closed.emit()

    def setDirty(self, x=True):
        self.dirty = x

    def text(self):
        return self.editor.text()

    def showConsole(self):
        sizes = self.splitter.sizes()
        if sizes[1] == 0:
            self.splitter.setSizes([sizes[0] - 200, 200])

    def showEditor(self):
        sizes = self.splitter.sizes()
        if sizes[0] == 0:
            self.splitter.setSizes([400, sizes[1] - 400])

    def appendConsole(self, s):
        self.console.append(s)

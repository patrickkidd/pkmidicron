from .pyqt_shim import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython


font = QFont('Andale Mono')
font.setPointSize(12)


class Editor(QsciScintilla):

    saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

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
        self.setMarginsBackgroundColor(QColor('#d6ffd0'))
        self.setMarginLineNumbers(1, True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setLexer(QsciLexerPython(self))

        self.setFont(font)
        # self.lexer().setPaper(QColor('red'))

        self.textChanged.connect(self.parent().setDirty)

        self.saveButton = QPushButton(tr('Save'), self)
        self.saveButton.clicked.connect(self.saved.emit)

        # self.saveAction = QAction(tr("Indent Selection"), self)
        # self.saveAction.setShortcut(QKeySequence(Qt.ShiftModifier | Qt.MetaModifier | Qt.Key_S))
        # self.saveAction.triggered.connect(self.saved.emit)
        # self.addAction(self.saveAction)

        self.indentAction = QAction(tr("Indent Selection"), self)
        self.indentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketRight))
        self.indentAction.triggered.connect(self.indentLineOrSelection)
        self.addAction(self.indentAction)
        
        self.unindentAction = QAction(tr("Unindent Selection"), self)
        self.unindentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketLeft))
        self.unindentAction.triggered.connect(self.unindentLineOrSelection)
        self.addAction(self.unindentAction)

        self.resizeEvent(None)

    def resizeEvent(self, e):
        if e:
            super().resizeEvent(e)
        self.saveButton.move(self.width() - self.saveButton.width(), 0)

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
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFrameStyle(QFrame.NoFrame)
        self.setReadOnly(True)
        p = QPalette(self.palette())
        p.setColor(QPalette.Base, QColor('black'))
        p.setColor(QPalette.Text, QColor('yellow'))
        self.setPalette(p)
        self.setFont(font)

        self.clearButton = QPushButton(tr('Clear'), self)
        self.clearButton.clicked.connect(self.clear)

        self.resizeEvent(None)
    
    def resizeEvent(self, e):
        if e:
            super().resizeEvent(e)
        self.clearButton.move(self.width() - self.clearButton.width(), 0)



class ScriptEditor(QWidget):

    closed = pyqtSignal()
    saved = pyqtSignal()
    textChanged = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dirty = False

        self.editor = Editor(self)
        self.editor.saved.connect(self.saved.emit)
        self.editor.textChanged.connect(self.textChanged.emit)

        self.console = Console(self)

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

    def appendConsole(self, s):
        self.console.append(s)

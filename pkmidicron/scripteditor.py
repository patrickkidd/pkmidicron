from .pyqt_shim import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

class ScriptEditor(QsciScintilla):

    closed = pyqtSignal()
    saved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dirty = False
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
        self.setMarginsBackgroundColor(QColor('white'))
        self.setMarginLineNumbers(1, True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setLexer(QsciLexerPython(self))

        f = QFont('Andale Mono')
        f.setPointSize(12)
        self.setFont(f)
        # self.lexer().setPaper(QColor('red'))

        self.textChanged.connect(self.setDirty)

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
        self.saveButton.move(self.width() - self.saveButton.width(), 0)

    def showEvent(self, e):
        self.resizeEvent(None)

    def setFont(self, f):
        super().setFont(f)
        self.lexer().setFont(f)

    def setDirty(self, x=True):
        self.dirty = x

    def closeEvent(self, e):
        self.closed.emit()

    def indentLineOrSelection(self):
        pass

    def unindentLineOrSelection(self):
        pass

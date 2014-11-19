from .pyqt_shim import *
from PyQt5.Qsci import QsciScintilla, QsciLexerPython

class ScriptEditor(QsciScintilla):

    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.dirty = False
        self.setProperty("canHaveFocus", True)
        self.viewport().setProperty("canHaveFocus", True)
        self.errorLine = self.markerDefine(QsciScintilla.Background)
  
        highlightColor = QColor('yellow')
        highlightColor.setAlpha(0.3921568627451)
      
        self.setMarkerBackgroundColor(highlightColor)
        self.setEolMode(QsciScintilla.EolUnix)
        self.setAutoIndent(True)
        self.setIndentationWidth(4)
        self.setIndentationsUseTabs(False)
        self.setLexer(QsciLexerPython(self))
        self.setMarginWidth(1, 5)
        self.setMarginsBackgroundColor(QColor('white'))

        f = QFont('Andale Mono')
        f.setPointSize(12)
        self.setFont(f)
        # self.lexer().setPaper(QColor('red'))

        self.textChanged.connect(self.setDirty)

        self.indentAction = QAction(tr("Indent Selection"), self)
        self.indentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketRight))
        self.indentAction.triggered.connect(self.indentLineOrSelection)
        self.addAction(self.indentAction)
        
        self.unindentAction = QAction(tr("Unindent Selection"), self)
        self.unindentAction.setShortcut(QKeySequence(Qt.MetaModifier | Qt.Key_BracketLeft))
        self.unindentAction.triggered.connect(self.unindentLineOrSelection)
        self.addAction(self.unindentAction)

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

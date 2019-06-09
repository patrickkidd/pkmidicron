import sys
from pkmidicron.pyqt_shim import *
#from pkmidicron.scripteditor import *


is_white = True

class O(QObject):
    def eventFilter(self, o, e):
        global is_white, w
        if e.type() == QEvent.InputMethodQuery:
            is_white = not is_white
            if is_white:
                c = QColor('red')
            else:
                c = QColor('green')
            p = QPalette(w.palette())
            p.setColor(QPalette.Base, c)
            w.setPalette(p)
            return True
        return super().eventFilter(o, e)


class W(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
    def __del__(self):
        print('__del__')
    def mousePressEvent(self, e):
        print('click')
        self.close()



SOURCE = """
class A:
    def __del__(self):
        print('__del__')
a = A()
"""


app = QApplication(sys.argv)
w1 = W()
w1.show()
w2 = W()
w2.show()
#w.setText(SOURCE)
#w.editor.setExceptionLine(3)
#w.show()
#w = QTextEdit()
#w.show()
#ef = O()
#w.installEventFilter(ef)
app.exec()

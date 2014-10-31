from pyqt_shim import QUndoCommand


class AddBinding(QUndoCommand):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw
        self.mw.addBinding()

    def undo(self):
        self.mw.removeBinding()

    def redo(self):
        self.mw.addBinding()

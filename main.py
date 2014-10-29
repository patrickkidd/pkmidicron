#!/usr/bin/env python3

import os, sys
from pkmidicron import MainWindow, util
from pkmidicron.pyqt_shim import Qt, QSettings, QApplication, QIcon, QWidget, QLibraryInfo, QFileSystemWatcher

STYLE_SHEET = """
QLineEdit:read-only {
    border: 0;
    background: transparent;
}
QListView::item {
    border-bottom: 1px solid #ececec;
}
QListView::item:selected {
    background: #3875D7;
}
_CollapsableBox, _Action {
    border: 1px solid grey;
    border-radius: 5px;
    background: lightGrey;
}

ActionWidget[selected="true"] {
    background: grey;
}
Simulator {
    border-radius: 5px;
}
"""


def main():
    import rtmidi
    prefs = util.Settings('vedanamedia', 'PKMidiCron')
    prefs.setAutoSave(True)
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    def setStyleSheet():
#        print('setStyleSheet')
#        text = open(styleSheet).read()
        app.setStyleSheet(STYLE_SHEET)
#    styleSheet = os.path.join("pkmidicron", "app.css")
#    watcher = QFileSystemWatcher([styleSheet])
#    watcher.fileChanged.connect(setStyleSheet)
    setStyleSheet()

    try:
        w = MainWindow(prefs)
        w.show()
        app.exec()
    except:
        print()
        import traceback
        exc = sys.exc_info()
        traceback.print_tb(exc[2])
        print(exc[0].__name__ + ':', exc[1])
        print()
    rtmidi.CollectorBin.cleanup()
main()

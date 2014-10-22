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
CollapsableBox, Action {
    border: 1px solid grey;
    border-radius: 5px;
    background: lightGrey;
}

ActionWidget[selected="true"] {
    background: grey;
}
"""


def main():
    import rtmidi
    settings = QSettings('vedanamedia', 'PKMidiCron')
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    def setStyleSheet():
        print('setStyleSheet')
#        text = open(styleSheet).read()
        app.setStyleSheet(STYLE_SHEET)
#    styleSheet = os.path.join("pkmidicron", "app.css")
#    watcher = QFileSystemWatcher([styleSheet])
#    watcher.fileChanged.connect(setStyleSheet)
    setStyleSheet()

    try:
        w = MainWindow(settings)
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

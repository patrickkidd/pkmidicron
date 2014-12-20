#!/usr/bin/env python3

import os, sys
#import rtmidi
#rtmidi.DEBUG = True
from pkmidicron import MainWindow, util, ports
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
QToolButton {
    background: transparent;
}
"""



def main():
    import rtmidi
    prefs = util.Settings('vedanamedia', 'PKMidiCron')
    print('PREFERENCES: ', prefs.fileName())
    prefs.setAutoSave(True)
    app = util.Application(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setQuitOnLastWindowClosed(False)

    def setStyleSheet():
#        print('setStyleSheet')
#        text = open(styleSheet).read()
        app.setStyleSheet(STYLE_SHEET)
#    styleSheet = os.path.join("pkmidicron", "app.css")
#    watcher = QFileSystemWatcher([styleSheet])
#    watcher.fileChanged.connect(setStyleSheet)
    setStyleSheet()
    ports.inputs(app, prefs)
    ports.outputs(app, prefs)

    w = None
    try:
        w = MainWindow(prefs)
        if prefs.value('MainWindowShown', type=bool, defaultValue=True):
            w.show()
        else:
            w.trayIcon.showHello()
        app.exec()
    except:
        print()
        import traceback
        exc = sys.exc_info()
        traceback.print_tb(exc[2])
        print(exc[0].__name__ + ':', exc[1])
        print()
    ports.cleanup()
    if w:
        w.cleanup()
    rtmidi.CollectorBin.cleanup()
main()

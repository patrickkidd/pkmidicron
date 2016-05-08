#!/usr/bin/env python3

import os, sys
#import rtmidi
#rtmidi.DEBUG = True
from pkmidicron import MainWindow, util, ports
from pkmidicron.pyqt_shim import Qt, QSettings, QApplication, QIcon, QWidget, QLibraryInfo, QFileSystemWatcher, QFile, QCoreApplication

STYLE_SHEET = """
QLineEdit:read-only {
    border: 0;
    background: transparent;
}
QLineEdit {
    padding-left: 1px;
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
#    isDefault = not QFile(prefs.fileName()).exists()
#    print('PREFERENCES (isDefault: %s): %s' % (isDefault, prefs.fileName()))
#    for key in prefs.allKeys():
#        if key.startswith('InputPorts'):
#            print(key, prefs.value(key))
    prefs.setAutoSave(True)
    app = util.Application(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setQuitOnLastWindowClosed(False)
    # print(app.applicationDirPath())
        
    # delete update slugs on windows
    exe = QCoreApplication.applicationFilePath()
    if exe.endswith('.exe'):
        slug = os.path.join(os.path.dirname(exe), 'deleteme.exe')
        if QFile(slug).exists():
            print('deleting update slug...')
            QFile(slug).remove()
    
    def setStyleSheet():
#        print('setStyleSheet')
#        text = open(styleSheet).read()
        app.setStyleSheet(STYLE_SHEET)
#    styleSheet = os.path.join("pkmidicron", "app.css")
#    watcher = QFileSystemWatcher([styleSheet])
#    watcher.fileChanged.connect(setStyleSheet)
    setStyleSheet()
    ports.Network.instance(prefs)
    ports.inputs(app, prefs)
    ports.outputs(app, prefs)

    w = None
    retVal = None
    try:
        w = MainWindow(prefs)
        if prefs.value('MainWindowShown', type=bool, defaultValue=True):
            w.show()
        else:
            w.trayIcon.showHello()
        retVal = app.exec()
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
#    if retVal is not None:
#        sys.exit(retVal)
main()

#!/usr/bin/env python3

import sys
from pkmidicron import MainWindow, util
from pkmidicron.pyqt_shim import Qt, QSettings, QApplication, QIcon, QWidget, QLibraryInfo


def main():
    if hasattr(sys, 'frozen'):
        def SetPaths():
            print("ADDING PLUGIN PATH")
            QApplication.addLibraryPath("./platforms")
            paths = QApplication.libraryPaths()
            for p in paths:
                if '/usr/local/Cellar/' in p:
                    QApplication.removeLibraryPath(p)
            print(QApplication.libraryPaths())
            loc = QLibraryInfo.location(QLibraryInfo.PluginsPath)
            print('>>>>', loc)
#        SetPaths()

    import rtmidi
    settings = QSettings('vedanamedia', 'PKMidiCron')
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
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

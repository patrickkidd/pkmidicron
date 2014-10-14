#!/usr/bin/env python3

import sys
from pyqt_shim import QSettings, QApplication, QIcon, QWidget
from pkmidicron import MainWindow
import util


class Mine(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.one = QWidget(self)
        self.one.setMinimumHeight(100)
        util.setBackgroundColor(self.one, Qt.green)

        self.two = QWidget(self)
        util.setBackgroundColor(self.two, Qt.blue)

        lowerLayout = QHBoxLayout()
        self.two.setLayout(lowerLayout)

        for i in range(5):
            b = QPushButton('bleh %s' % i, self.two)
            lowerLayout.addWidget(b)

        Layout = QVBoxLayout()
        self.setLayout(Layout)
        Layout.addWidget(self.one)
        Layout.addWidget(self.two)

        Layout.setContentsMargins(0, 0, 0, 0)
        Layout.setSpacing(0)



def main():
    settings = QSettings('vedanamedia', 'PKMidiCron')
    app = QApplication(sys.argv)
    icon = QIcon('om-128px.png')
    app.setWindowIcon(icon)
    w = MainWindow(settings)
    w.show()
    app.exec()
main()

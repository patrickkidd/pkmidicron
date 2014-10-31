import sys
from pkmidicron import util, ports
from PyQt5.QtCore import QCoreApplication

import signal
def sigint_handler(*args):
    QCoreApplication.quit()
signal.signal(signal.SIGINT, sigint_handler)

def added(name):
    print('ADDED >>>%s<<<<' % name)
def removed(name):
    print('REMOVED >>>%s<<<' % name)

app = QCoreApplication(sys.argv)
ports = ports.ports()
ports.portAdded.connect(added)
ports.portRemoved.connect(removed)
app.exec()

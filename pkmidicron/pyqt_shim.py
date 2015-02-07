#import module_locator
#if module_locator.we_are_frozen():
#    print("frozen")
#    DIRNAME = os.path.dirname(os.path.realpath(sys.argv[0]))
#    os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(DIRNAME, 'platforms')
#    print("QT_QPA_PLATFORM_PLUGIN_PATH = " +  os.path.join(DIRNAME, 'platforms'))
#else:
#    print("not frozen")


from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtNetwork import *
# cx_Freeze workaround
import PyQt5.QtPrintSupport

def tr(s):
    return QCoreApplication.translate('A', s)

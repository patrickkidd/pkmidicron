from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import time

settings = QSettings('./test-prefs')
print(settings.value('mine', type=int))
settings.setValue('mine', time.time())
del settings

import os
import sys
from cx_Freeze import setup, Executable


options = {}

if hasattr(os, 'uname'):
    base = None
    targetName = 'PKMidiCron'
    options['bdist_mac'] = {
        "iconfile": "icon.icns",
        "bundle_name": "PKMidiCron",
        "custom_info_plist": "Info.plist",
        #"qt_menu_nib": "/Applications/Qt-5.3/5.3/Src/qtbase/src/plugins/platforms/cocoa/qt_menu.nib"
        "qt_menu_nib": "/usr/local/Cellar/qt5/5.6.0/qt_menu.nib"
    }
#    options['build_exe'] = {
#        "includes": ['_frozen_importlib_external'],
#    }
else:
    sysPackages = [i for i in sys.path if 'site-packages' in i][0]
    options['build_exe']['include_files'].append(*[
        os.path.relpath(os.path.join(sysPackages, 'PyQt5\LibEGL.dll'))
    ])
    options['build_exe'] = {
        "packages": ["os"],
        "excludes": ["tkinter"],
        "include_files": [],
        "icon": "icon.ico",
    }
    base = None
    # Comment out for a console app
    #if sys.platform == "win32":
    #    base = "Win32GUI"
    targetName = 'PKMidiCron.exe'


def get_data_files():
    return [('', [])]

setup(  name = "PKMidiCron",
        version = "0.1",
        description = "Trigger the triggers!",
        options = options,
        executables = [
            Executable(
                "PKMidiCron.py",
                targetName=targetName,
                base=base
            )
        ],
        data_files=get_data_files())

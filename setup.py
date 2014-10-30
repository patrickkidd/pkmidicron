import os
import sys
from cx_Freeze import setup, Executable



options = {
    # Dependencies are automatically detected, but it might need fine tuning.
    "build_exe": {
        "packages": ["os"],
        "excludes": ["tkinter"],
        "include_files": []
    },
    "bdist_mac": {
        "iconfile": "icon.icns",
        "bundle_name": "PKMidiCron",
        "custom_info_plist": "Info.plist",
        "qt_menu_nib": "/Applications/Qt-5.3/5.3/Src/qtbase/src/plugins/platforms/cocoa/qt_menu.nib"
    }
}

if hasattr(os, 'uname'):
    base = None
    targetName = 'PKMidiCron'
else:
    sysPackages = [i for i in sys.path if 'site-packages' in i][0]
    options['build_exe']['include_files'].append(*[
        os.path.relpath(os.path.join(sysPackages, 'PyQt5\LibEGL.dll'))
    ])
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
                "main.py",
                targetName=targetName,
                base=base
            )
        ],
        data_files=get_data_files())

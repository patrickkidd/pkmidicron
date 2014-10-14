import os
import sys
from cx_Freeze import setup, Executable


if hasattr(os, 'uname'):
    OSNAME = os.uname()[0]
else:
    OSNAME = 'Windows'

base = None
options = {
    # Dependencies are automatically detected, but it might need fine tuning.
    "build_exe": {
        "packages": ["os"],
        "excludes": ["tkinter"],
        "include_files": [],
        "icon": "om-128px.png"
    }
}

if OSNAME == 'Windows':
    build_exe_options['include_files'] = [
        os.path.relpath('C:\Python34\Lib\site-packages\PyQt5\LibEGL.dll')
    ]
    # Comment out for a console app
    #if sys.platform == "win32":
    #    base = "Win32GUI"


def get_data_files():
    return [('', [])]

setup(  name = "PKMidiCron",
        version = "0.1",
        description = "Trigger the triggers!",
        options = options,
        executables = [
            Executable(
                "main.py",
                targetName="PKMidiCron",
                base=base
            )
        ],
        data_files=get_data_files())

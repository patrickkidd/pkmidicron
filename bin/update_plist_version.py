
import os, os.path, sys, plistlib

ROOT = os.path.realpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

sys.path.append(ROOT)

from pkdiagram import version

osx_plist = os.path.join(ROOT, 'build', 'osx-config', 'Info.plist')
ios_plist = os.path.join(ROOT, 'build', 'ios-config', 'Info.plist')

for fpath in [osx_plist, ios_plist]:
    print('Patching', fpath, 'to version', version.VERSION)
    # plutil -replace CFBundleVersion -string '0.1.0d1' build/osx-config/Info.plist && less build/osx-config/Info.plist 
    cmd = "plutil -replace CFBundleVersion -string '%s' %s" % (version.VERSION, osx_plist)
    print(cmd)
    os.system(cmd)
    cmd = "plutil -replace CFBundleShortVersionString -string '%s' %s" % (version.VERSION, osx_plist)
    print(cmd)
    os.system(cmd)


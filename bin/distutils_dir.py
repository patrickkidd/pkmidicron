import os, sys, platform

if os.name == 'posix':
    mac_parts = platform.mac_ver()[0].split('.')
    py_parts = sys.version.split()[0].split('.')
    s = "lib.macosx-%s.%s-x86_64-%s.%s" % (mac_parts[0], mac_parts[1], py_parts[0], py_parts[1])

print(s)


##
## NO DEPENDENCIES!!
##

from .build_uuid import *

BETA_SUFFIX = 0
VERSION_MAJOR = 1
VERSION_MINOR = 2
VERSION_MICRO = 1
VERSION_SUFFIX = BETA_SUFFIX and 'b%s' % BETA_SUFFIX or ''
VERSION_SHORT = "%s.%s.%s" % (VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO)
VERSION = '%s.%s.%s%s' % (VERSION_MAJOR, VERSION_MINOR, VERSION_MICRO, VERSION_SUFFIX)
VERSION_COMPAT = '1.0.0b7' # oldest version that this version can open. Bump when adding features that are not backward compatible.
IS_BETA = bool(BETA_SUFFIX)

VERSION_URL = QUrl('http://vedanamedia.com/products/pkmidicron/version.txt')
    
def verint(a, b, c, beta=None):
    # print('verint', a, b, c, type(a), type(b), type(c))
    return (a << 24) | (b << 16) | c

def split(text):
    text = text.strip()
    major, minor, micro = [i for i in text.split('.')]
    beta = None
    if 'b' in micro:
        micro, beta = micro.split('b')
        beta = int(beta)
    major, minor, micro = int(major), int(minor), int(micro)
    return major, minor, micro, beta

def greaterThan(textA, textB):
    majorA, minorA, microA, betaA = split(textA)
    majorB, minorB, microB, betaB = split(textB)
    verA = verint(majorA, minorA, microA)
    verB = verint(majorB, minorB, microB)
    if verA == verB:
        if betaA and betaB:
            return (betaA > betaB)
        else:
            return False
    else:
        return verA > verB

def greaterThanOrEqual(textA, textB):
    majorA, minorA, microA, betaA = split(textA)
    majorB, minorB, microB, betaB = split(textB)
    verA = verint(majorA, minorA, microA)
    verB = verint(majorB, minorB, microB)
    if verA == verB:
        if betaA and betaB:
            return (betaA >= betaB)
        else:
            return False
    else:
        return verA > verB

def lessThan(textA, textB):
    return greaterThan(textB, textA)    

def lessThanOrEqual(textA, textB):
    return greaterThanOrEqual(textB, textA)    

def ___updateAvailable(text):
    return greaterThan(text, VERSION)


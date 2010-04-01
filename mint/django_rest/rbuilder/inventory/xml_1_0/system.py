#!/usr/bin/env python

#
# Generated  by generateDS.py.
#

import sys
from string import lower as str_lower
from xml.dom import minidom

import supers_system as supermod

#
# Globals
#

ExternalEncoding = 'utf-8'

#
# Data representation classes
#

class systemTypeSub(supermod.systemType):
    def __init__(self, generatedUUID=None, localUUID=None, registrationDate=None, systemName=None, memory=None, osType=None, osMajorVersion=None, osMinorVersion=None, topLevelGroup=None, flavor=None, systemType=None, sslClientCertificate=None, sslClientKey=None, sslServerCertificate=None):
        supermod.systemType.__init__(self, generatedUUID, localUUID, registrationDate, systemName, memory, osType, osMajorVersion, osMinorVersion, topLevelGroup, flavor, systemType, sslClientCertificate, sslClientKey, sslServerCertificate)
supermod.systemType.subclass = systemTypeSub
# end class systemTypeSub



def parse(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.systemType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_="system",
##         namespacedef_='')
    doc = None
    return rootObj


def parseString(inString):
    doc = minidom.parseString(inString)
    rootNode = doc.documentElement
    rootObj = supermod.systemType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('<?xml version="1.0" ?>\n')
##     rootObj.export(sys.stdout, 0, name_="system",
##         namespacedef_='')
    return rootObj


def parseLiteral(inFilename):
    doc = minidom.parse(inFilename)
    rootNode = doc.documentElement
    rootObj = supermod.systemType.factory()
    rootObj.build(rootNode)
    # Enable Python to collect the space used by the DOM.
    doc = None
##     sys.stdout.write('#from supers_system import *\n\n')
##     sys.stdout.write('import supers_system as model_\n\n')
##     sys.stdout.write('rootObj = model_.system(\n')
##     rootObj.exportLiteral(sys.stdout, 0, name_="system")
##     sys.stdout.write(')\n')
    return rootObj


USAGE_TEXT = """
Usage: python ???.py <infilename>
"""

def usage():
    print USAGE_TEXT
    sys.exit(1)


def main():
    args = sys.argv[1:]
    if len(args) != 1:
        usage()
    infilename = args[0]
    root = parse(infilename)


if __name__ == '__main__':
    #import pdb; pdb.set_trace()
    main()



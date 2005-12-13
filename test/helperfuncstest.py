#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

import kid
import os
from mint import templates

from mint_rephelp import MintRepositoryHelper
from mint.userlevels import myProjectCompare

testTemplate = \
"""<?xml version='1.0' encoding='UTF-8'?>
<plain>This is a plain text ${myString}.</plain>
"""

class ProjectTest(MintRepositoryHelper):
    def testMyProjectCompare(self):
        if not isinstance(myProjectCompare(('not tested', 1),
                                           ('ignored', 0)), int):
            self.fail("myProjectCompare did not return an int")
        if not isinstance(myProjectCompare(('not tested', 1L),
                                           ('ignored', 0L)), int):
            self.fail("myProjectCompare did not return an int")

    def compareMakefile(self, directory, exclusionList = []):
        makeFile = open(directory + '/Makefile')
        data = [ x.strip() for x in makeFile.read().split('\n')]
        makeFile.close()
        newData = []
        found = False
        continuedLine = ''
        for line in data:
            if line.endswith('\\'):
                continuedLine += line
            else:
                newData.append(continuedLine + line)
                continuedLine = ''
        fileList = []
        for line in newData:
            if line.startswith('python_files') or line.startswith('kid_files'):
                fileList.extend([''.join(x.strip().split('\\')) for x in \
                             ' '.join((line.split('=')[1] \
                                       ).split('\t')).split(' ') \
                             if x.strip() != ''])
        fileList = sorted(fileList)
        actualList = sorted([x for x in os.listdir(directory) \
                             if (x.endswith('.py') or x.endswith('.kid'))])
        missingList = [x for x in actualList if (x not in fileList) \
                       and (x not in exclusionList)]
        if missingList:
            self.fail("Makefile: %s is missing the following files: %s" %
                      (directory + '/Makefile', str(missingList)))

    def testMakefiles(self):
        skipDirs = ('test/archive/arch', 'test/archive/use',
                    'mint/web/content', '.hg')
        for dirPath, dirNames, fileNames in \
                os.walk(os.getenv('MINT_PATH')):
            if "Makefile" not in fileNames:
                ignore = False
                for skipDir in skipDirs:
                    if dirPath.startswith(os.getenv('MINT_PATH') + skipDir):
                        ignore = True
                        break
                if not ignore:
                    self.fail("%s is missing a Makefile" % dirPath)
            else:
                self.compareMakefile(dirPath)

    def testPlainKidTemplate(self):
        t = kid.Template(testTemplate)
        t.myString = "string"
        
        render = templates.write(t)
        assert render == "This is a plain text string."


if __name__ == "__main__":
    testsuite.main()

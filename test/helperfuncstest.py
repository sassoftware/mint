#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

import kid
import os
import sys
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

    def compareMakefile(self, directory, exclusionList = set()):
        missing = False
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
                
        fileList = set() 
        for line in newData:
            if line.startswith('python_files') or line.startswith('kid_files') or line.startswith('script_dist'):
                fileList |= set(''.join(x.strip().split('\\')) for x in \
                             ' '.join((line.split('=')[1] \
                                       ).split('\t')).split(' ') \
                             if x.strip() != '')

        actualList = set(x for x in os.listdir(directory) \
                           if ((x.endswith('.py') or x.endswith('.kid')) \
                             and not x.startswith(".")))
        missingList = (actualList - exclusionList) - fileList
        
        if missingList:
            print >> sys.stderr, "\n%s is missing: %s" % \
                  (directory + '/Makefile', ' '.join(missingList)),
            missing = True
        return missing

    def testMakefiles(self):
        missing = False
        skipDirs = ('test/archive/arch', 'test/archive/use',
                    'mint/web/content', '.hg', 'scripts/DiskImageData')
        for dirPath, dirNames, fileNames in \
                os.walk(os.getenv('MINT_PATH')):
            if "Makefile" not in fileNames:
                ignore = False
                for skipDir in skipDirs:
                    if dirPath.startswith(os.getenv('MINT_PATH') + skipDir):
                        ignore = True
                        break
                if not ignore:
                    print >> sys.stderr, "\n%s is missing Makefile" % dirPath,
                    missing = True
            else:
                missing = max(missing, self.compareMakefile(dirPath))
        if missing:
            print >> sys.stderr, ''
        self.failIf(missing, "There are issues with Makefiles")

    def testPlainKidTemplate(self):
        t = kid.Template(testTemplate)
        t.myString = "string"

        render = templates.write(t)
        assert render == "This is a plain text string."

    def testExplicitTransactions(self):
        if self.mintCfg.dbDriver != 'sqlite':
            raise testsuite.SkipTestException
        cu = self.db.cursor()

        # dbstore explicit transaction method
        self.db.transaction()
        assert(self.db.dbh.inTransaction)
        self.db.rollback()

if __name__ == "__main__":
    testsuite.main()

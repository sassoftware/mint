#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
import unittest
testsuite.setup()

import kid
import os
import sys
from mint import templates
from mint.helperfuncs import truncateForDisplay
from mint.userlevels import myProjectCompare

testTemplate = \
"""<?xml version='1.0' encoding='UTF-8'?>
<plain>This is a plain text ${myString}.</plain>
"""
testTemplateWithConditional = \
"""<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns#">
<div py:if="isChunky">${myString}</div>
<div py:if="not isChunky">Not ${myString}</div>
</plain>
"""

class HelperFunctionsTest(unittest.TestCase):
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
        skipDirs = ('.hg', 'test/archive/arch', 'test/archive/use',
                    'mint/web/content', 'scripts/DiskImageData',
                    'scripts/servertest', 'test/templates')
        mint_path = os.getenv('MINT_PATH')
        if not mint_path:
            print >> sys.stderr, "MINT_PATH is missing from your environment"
            raise testsuite.SkipTestException()
        for dirPath, dirNames, fileNames in os.walk(mint_path):
            if "Makefile" not in fileNames:
                ignore = False
                for skipDir in skipDirs:
                    if dirPath.startswith(os.path.join(mint_path, skipDir)):
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

    def testPlainKidTemplateWithConditional(self):
        t = kid.Template(testTemplateWithConditional)
        t.myString = "Chunky bacon"
        t.isChunky = True
        render = templates.write(t)
        print render
        self.assertEqual(render.find("Not"), -1)

    def testPlainKidTemplateWithImport(self):
        import kid
        kid.enable_import()
        from templates import plainTextTemplate
        render = templates.write(plainTextTemplate, myString = "dubious text")
        self.assertEqual(render, "This is a string containing dubious text.")

    def testExplicitTransactions(self):
        from conary import dbstore
        db = dbstore.connect(":memory:", "sqlite")
        cu = db.cursor()

        # dbstore explicit transaction method
        db.transaction()
        assert(db.dbh.inTransaction)
        db.rollback()

    # Test strings with the default values
    def testTruncateKnownGoodValues(self):
        # Test values (assumes maxWords=10 and maxWordLen=15)
        knownGoodValues = (
              # empty test
              ( "", "" ),

              # a single long word
              ( "Supercalifragilisticexpialidocious!", "Supercalifragil..." ),

              # the raison d'etre
              ( "Woooooooooooooooooooooooooooooooooooooooooooooooooooooooooooo"
                "oooooooooooooooooooooooooooooooot", "Woooooooooooooo..." ),

              # a simple phrase
              ( "I like pork!", "I like pork!" ),

              # a sample block of text
              ( "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
                "Pellentesque ullamcorper tincidunt sem. Pellentesque ultricies"
                "lacinia ante. Proin molestie ligula ut.",
                "Lorem ipsum dolor sit amet, consectetuer adipiscing elit. "
                "Pellentesque ullamcorper ....")
        )

        for input, expectedOutput in knownGoodValues:
            actualOutput = truncateForDisplay(input)
            self.assertEqual(actualOutput, expectedOutput)

    # Test different values for maxWordsLen
    def testTruncateDifferentMaxWordLengths(self):
        s = "012345678901234567890123456789"
        self.assertEqual(truncateForDisplay(s, 10, 20), s[0:20]+'...')
        self.assertEqual(truncateForDisplay(s, 10, 10), s[0:10]+'...')
        self.assertEqual(truncateForDisplay(s, 10, 5), s[0:5]+'...')
        self.assertEqual(truncateForDisplay(s, 10, 1), s[0:1]+'...')
        self.assertEqual(truncateForDisplay(s, 10, 400), s)

    # Test different values for maxWords
    def testTruncateDifferentMaxWords(self):
        s = "I am a string of some words. Fear me!"
        self.assertEqual(truncateForDisplay(s, 1), "I ....")
        self.assertEqual(truncateForDisplay(s, 2), "I am ....")
        self.assertEqual(truncateForDisplay(s, 400), s)

    # Test a weird sentence of mostly punctuation
    def testTruncatePathologicalSentences(self):
        s = "#*$)(#*$)@Q$)@*$)%*#! #$)#*$)( $# $#*(!!!!"
        self.assertEqual(truncateForDisplay(s), s[0:15]+'...')

    # Make sure we raise appropriately if we are called with bad args
    def testTruncateBadCalls(self):
        self.failUnlessRaises(ValueError, truncateForDisplay, "Foo", -1)
        self.failUnlessRaises(ValueError, truncateForDisplay, "Foo",  0)
        self.failUnlessRaises(ValueError, truncateForDisplay, "Foo", -1, -1)
        self.failUnlessRaises(ValueError, truncateForDisplay, "Foo", -1, 0)

if __name__ == "__main__":
    testsuite.main()

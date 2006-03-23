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
import time
import tempfile

from mint import templates
from mint.helperfuncs import truncateForDisplay, extractBasePath, \
        hostPortParse, rewriteUrlProtocolPort
from mint.userlevels import myProjectCompare
from mint.mint import timeDelta
from mint.distro import jsversion
from mint_rephelp import MINT_PROJECT_DOMAIN

from conary.lib import util

testTemplate = \
"""<?xml version='1.0' encoding='UTF-8'?>
<plain>This is a plain text ${myString}.</plain>
"""
testTemplateWithConditional = \
"""<?xml version='1.0' encoding='UTF-8'?>
<plain xmlns:py="http://purl.org/kid/ns%s">
<div py:if="isChunky">${myString}</div>
<div py:if="not isChunky">Not ${myString}</div>
</plain>
""" % '#'

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
                    'mint/web/content', 'scripts', 'test/templates',
                    'test/annotate')
        mint_path = os.getenv('MINT_PATH')

        # tweak skipdirs to be fully qualified path
        skipDirs = [os.path.join(mint_path, x) for x in skipDirs]
        if not mint_path:
            print >> sys.stderr, "MINT_PATH is missing from your environment"
            raise testsuite.SkipTestException()
        for dirPath, dirNames, fileNames in \
            [x for x in os.walk(mint_path) \
             if True not in [x[0].startswith(y) for y in skipDirs]]:
            if "Makefile" not in fileNames:
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

    def testTimeDelta(self):
	ct = time.time()
	assert(timeDelta(0) == "Never")
	assert(timeDelta(ct, ct) == "This very second")
	assert(timeDelta(ct - 30, ct) == "30 seconds ago")
	assert(timeDelta(ct - 60, ct) == "1 minute ago")
	assert(timeDelta(ct - 974, ct) == "16 minutes ago")
	assert(timeDelta(ct - 3650, ct) == "1 hour ago")
	assert(timeDelta(ct - 12459, ct) == "3 hours ago")
	assert(timeDelta(ct - 100234, ct) == "Yesterday")
	assert(timeDelta(ct - 373123, ct) == "4 days ago")
	assert(timeDelta(ct - 2592000, ct) == 
               time.strftime('%d-%b-%Y', time.localtime(ct - 2592000)))

    def testExtractBasePath(self):
        assert(extractBasePath("/", "/") == "/")
        assert(extractBasePath("/foo", "/foo") == "/")
        assert(extractBasePath("/rbuilder/", "/") == "/rbuilder/")
        assert(extractBasePath("/rbuilder/foo", "/foo") == "/rbuilder/")

    def testJsVersions(self):
        tmpDir = tempfile.mkdtemp()
        try:
            for dir in ('15.20.1', '1.5', '10.20', '10.2', '1.5.4beta', '1A',
                        'README'):
                os.mkdir(os.path.join(tmpDir, dir))
            for fName in ('FOO', '1.5.4'):
                f = open(os.path.join(tmpDir, fName), 'w')
                f.close()
            self.failIf(jsversion.getVersions(tmpDir) !=
                        ['1.5', '1.5.4beta', '10.2', '10.20', '15.20.1'],
                        "Version list contained improper job server versions.")
            self.failIf(jsversion.getDefaultVersion(tmpDir) != '15.20.1',
                        "Wrong default job server version.")

            specStrings = ('trove=/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/1.0.0-1-1',
                           'trove=/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/1.5.4-1-1',
                           'trove=/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/2.0.3-1-1',)
            f = open(os.path.join(tmpDir, 'versions'), 'w')
            f.write('\n'.join(specStrings))
            f.close()
            self.failIf(jsversion.getVersions(tmpDir) !=
                        ['1.0.0', '1.5.4', '2.0.3'],
                        "Versions file did not override directories")
            self.failIf(jsversion.getDefaultVersion(tmpDir) != '2.0.3',
                        "Wrong default job server version.")
        finally:
            util.rmtree(tmpDir)

    def testHostPortParse(self):
        self.assertEqual(hostPortParse('foo.bar.baz:80', 80),
                ('foo.bar.baz', 80))
        self.assertEqual(hostPortParse('foo.bar.baz:8080', 80),
                ('foo.bar.baz', 8080))
        self.assertEqual(hostPortParse('foo.bar.baz', 443),
                ('foo.bar.baz', 443))

    def testHostnamePortParseBadCalls(self):
        self.failUnlessRaises(ValueError, hostPortParse, "", 80)
        self.failUnlessRaises(ValueError, hostPortParse, None, 80)

    def testRewriteUrlProtocolPort(self):
        url = 'http://a.special.somewhere.org/happy/happy/joy/joy/'
        urlSSL = 'https://vault.fortknox.gov/'

        # these shouldn't mutate the URL at all (default ports)
        self.assertEqual(rewriteUrlProtocolPort(url, 'http', 80), url)
        self.assertEqual(rewriteUrlProtocolPort(urlSSL, 'https', 443), urlSSL)

        # these replace the protocol using default ports
        self.assertEqual(rewriteUrlProtocolPort(url, 'https', 443),
                'https://a.special.somewhere.org/happy/happy/joy/joy/')
        self.assertEqual(rewriteUrlProtocolPort(urlSSL, 'http', 80),
                'http://vault.fortknox.gov/')

        # these replace the protocol and port
        self.assertEqual(rewriteUrlProtocolPort(url, 'https', 10000),
                'https://a.special.somewhere.org:10000/happy/happy/joy/joy/')
        self.assertEqual(rewriteUrlProtocolPort(urlSSL, 'http', 20000),
                'http://vault.fortknox.gov:20000/')


if __name__ == "__main__":
    testsuite.main()

#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
import unittest
testsuite.setup()

import fixtures

import kid
import os
import re
import sys
import tempfile
import time

from mint import constants
from mint import templates
from mint import server
from mint import flavors
from mint.helperfuncs import truncateForDisplay, extractBasePath, \
        hostPortParse, rewriteUrlProtocolPort, getArchFromFlavor
from mint.client import timeDelta
from mint import jsversion
from mint_rephelp import MINT_PROJECT_DOMAIN
from mint.userlevels import myProjectCompare
from mint.web import templatesupport

from conary.lib import util
from conary.deps import deps

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
                    'test/annotate', 'test/coverage', 'test/.coverage',
                    'test/archive/anaconda', 'bin', 'test')
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

    # Make sure we handle line breaks properly. We strip them out and do
    # not count them as a part of a word.
    def testTruncateWithLineBreaks(self):
        text = """I am a line. I am very expeditious.

Much like Powdermilk Biscuits[tm]."""
        self.assertEqual(truncateForDisplay(text), "I am a line. I am very expeditious. Much like ....")

    def testTimeDelta(self):
        # use hard coded time to prevent variable results based on
        # time of day when test is run.
        ct = 1143668527.7868781
	assert(timeDelta(0) == "Never")
        assert(timeDelta(0, capitalized = False) == "never")
	assert(timeDelta(ct, ct) == "This very second")
	assert(timeDelta(ct, ct, capitalized = False) == "this very second")
	assert(timeDelta(ct - 30, ct) == "30 seconds ago")
	assert(timeDelta(ct - 60, ct) == "1 minute ago")
	assert(timeDelta(ct - 974, ct) == "16 minutes ago")
	assert(timeDelta(ct - 3650, ct) == "1 hour ago")
	assert(timeDelta(ct - 12459, ct) == "3 hours ago")
	assert(timeDelta(ct - 100234, ct) == "Yesterday")
	assert(timeDelta(ct - 100234, ct, capitalized = False) == "yesterday")
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
            self.failIf(jsversion.getVersions(tmpDir) != [constants.mintVersion])

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
        url2 = 'http://bagel.to.go:39393/'
        urlSSL = 'https://vault.fortknox.gov/'

        # these shouldn't mutate the URL at all (default ports)
        self.assertEqual(rewriteUrlProtocolPort(url, 'http', 80), url)
        self.assertEqual(rewriteUrlProtocolPort(url, 'http'), url)
        self.assertEqual(rewriteUrlProtocolPort(url2, 'http'), url2)
        self.assertEqual(rewriteUrlProtocolPort(urlSSL, 'https', 443), urlSSL)
        self.assertEqual(rewriteUrlProtocolPort(urlSSL, 'https'), urlSSL)

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

    def testJavascript(self):
        scriptPath = os.path.join(os.path.split(os.path.split(\
            os.path.realpath(__file__))[0])[0], 'mint', 'web', 'content',
                                   'javascript')
        for library in \
                [x for x in os.listdir(scriptPath) if x.endswith('.js')]:
            libraryPath = os.path.join(scriptPath, library)
            f = open(libraryPath)
            docu = f.read()
            f.close()

            # strip multi-line comments.
            for comment in re.findall('/\*.*?\*/', docu, re.M | re.S):
                # we want to preserve newlines...
                newComment = '\n'.join(['' for x in comment.splitlines()])
                docu = docu.replace(comment, newComment)

            # recursively strip paren expressions
            expressions = re.findall('\([^()]*\)', docu)
            while expressions:
                for exp in expressions:
                    newExp = '^^^' + '\n'.join(['' for x in exp.splitlines()])\
                             + '~~~'
                    docu = docu.replace(exp, newExp)
                expressions = re.findall('\([^()]*\)', docu)
            docu = docu.replace('^^^', '(')
            docu = docu.replace('~~~', ')')
            # recursively strip bracket expressions
            expressions = re.findall('\[[^\[\]]*\]', docu)
            while expressions:
                for exp in expressions:
                    newExp = '^^^' + '\n'.join(['' for x in exp.splitlines()])\
                             + '~~~'
                    docu = docu.replace(exp, newExp)
                expressions = re.findall('\[[^\[\]]*\]', docu)
            docu = docu.replace('^^^', '[')
            docu = docu.replace('~~~', ']')
            lines = docu.split('\n')

            lines = zip(range(1, len(lines) + 1), lines)
            broken = False
            brokenLines = []
            for lineNum, line in lines:
                line = line.strip()
                match = re.search('//.*', line)
                if match:
                    comment = match.group()
                    newComment = '\n'.join(['' for x in comment.splitlines()])
                    line = line.replace(comment, newComment)
                line = line.strip()
                if line and line[-1] not in [';', '{', '}', '(', '[']:
                    broken = True
                    for tok in ('if', 'else', 'for', 'while', 'case',
                                'default'):
                        if line.startswith(tok):
                            broken = False
                    if broken:
                        brokenLines.append(lineNum)
            self.failIf(brokenLines,
                        "%s javascript syntax may be broken. " % library + \
                        "check lines: %s" % str(brokenLines))

    def testDictToJS(self):
        self.failIf(templatesupport.dictToJS({3: 2}) != "{'3': 2}",
                    "dict object with int keys converted incorrectly")
        self.failIf(templatesupport.dictToJS({'foo': 2}) != "{'foo': 2}",
                    "dict object with str keys converted incorrectly")

    def testCodeGeneration(self):
        from mint import buildtypes
        x = buildtypes.codegen()
        for name in buildtypes.typeNames.values():
            assert(name in x)

        from mint import jobstatus 
        x = jobstatus.codegen()
        for name in jobstatus.statusNames.values() + jobstatus.statusCodeNames.values():
            assert(name in x)

    def testScriptLogger(self):
        from mint import scriptlibrary
        import logging
        fd, fn = tempfile.mkstemp()

        try:
            scriptlibrary.setupScriptLogger(logfile = fn,
                consoleLevel = logging.ERROR  + 1)
            log = scriptlibrary.getScriptLogger()

            log.debug("Debug")
            log.info("Info")
            log.warning("Warning")
            log.error("Error")

            f = os.fdopen(fd, "r")
            logContents = f.read()
            for x in "Info", "Warning", "Error":
                assert(x in logContents)
        finally:
            os.unlink(fn)

    def testShortTroveSpec(self):
        from mint.web.templatesupport import shortTroveSpec

        # with a timestap
        assert(shortTroveSpec("foo=/bar@l:t/0.0:1.0-1-1[is:x86]") == "foo=1.0-1-1 (x86)")
        # without
        assert(shortTroveSpec("foo=/bar@l:t/1.0-1-1[is:x86]") == "foo=1.0-1-1 (x86)")

    def testGetArchFromFlavor(self):
        f_x86 = "1#x86:cmov:i486:i586:i686:~!mmx:~!sse2|5#use:~MySQL-python.threadsafe:X:~!alternatives:~!bootstrap:~!builddocs:~buildtests:desktop:dietlibc:emacs:gcj:~glibc.tls:gnome:~!grub.static:gtk:ipv6:kde:~!kernel.debug:~!kernel.debugdata:~!kernel.numa:krb:ldap:nptl:~!openssh.smartcard:~!openssh.static_libcrypto:pam:pcre:perl:~!pie:~!postfix.mysql:python:qt:readline:sasl:~!selinux:~sqlite.threadsafe:ssl:tcl:tcpwrappers:tk:~!xorg-x11.xprint"
        f_x86_64 = "1#x86_64:cmov:i486:i586:i686:~!mmx:~!sse2|5#use:~MySQL-python.threadsafe:X:~!alternatives:~!bootstrap:~!builddocs:~buildtests:desktop:dietlibc:emacs:gcj:~glibc.tls:gnome:~!grub.static:gtk:ipv6:kde:~!kernel.debug:~!kernel.debugdata:~!kernel.numa:krb:ldap:nptl:~!openssh.smartcard:~!openssh.static_libcrypto:pam:pcre:perl:~!pie:~!postfix.mysql:python:qt:readline:sasl:~!selinux:~sqlite.threadsafe:ssl:tcl:tcpwrappers:tk:~!xorg-x11.xprint"
        f_blank = ""
        f_no_arch = "#5:!tk"

        self.failUnlessEqual(getArchFromFlavor(f_x86), 'x86')
        self.failUnlessEqual(getArchFromFlavor(f_x86_64), 'x86_64')
        self.failUnlessEqual(getArchFromFlavor(f_blank), '')
        self.failUnlessEqual(getArchFromFlavor(f_no_arch), '')

    def testMaskedTests(self):
        curdir = os.path.normpath(__file__+ os.path.sep + '..')
        modules = [x for x in os.listdir(curdir) if x.endswith('test.py') \
                   and not x.startswith('.')]
        masked = False
        for fn in modules:
            f = open(curdir + os.path.sep + fn)
            lines = [x.strip() for x in f.readlines()]
            f.close()
            defLines = [x for x in lines if x.startswith('def')]
            defs = [x.split()[1].split('(')[0] for x in defLines]
            tests = [x for x in defs if x.startswith('test')]
            for test in set(tests):
                tests.remove(test)
            if tests:
                if not masked:
                    print >> sys.stderr, \
                          "\nWarning: test names have been resused."
                print >> sys.stderr, "%s: " % \
                      fn + ' '.join(tests)
            masked |= bool(tests)
        assert not masked

    def testExecTests(self):
        curdir = os.path.normpath(__file__+ os.path.sep + '..')
        modules = [x for x in os.listdir(curdir) if x.endswith('test.py') \
                   and not x.startswith('.')]
        nonExec = False
        for modl in modules:
            if not (os.stat(modl)[0] & 0100):
                if not nonExec:
                    print >> sys.stderr, ""
                print >> sys.stderr, "%s is not executable" % modl
                nonExec = True
        assert not nonExec

    def testGetStockFlavors(self):
        # make sure that pathSearchOrder contains all of the flavors in stockFlavors
        assert(set(flavors.pathSearchOrder) == set(flavors.stockFlavors.keys()))

        x86 = deps.ThawFlavor('1#x86:cmov:i486:i586:i686:~!mmx:~!sse2')
        x86_64 = deps.ThawFlavor('1#x86:i486:i586:i686:~!sse2|1#x86_64')

        assert(flavors.getStockFlavor(x86) == deps.parseFlavor(flavors.stockFlavors['1#x86']))
        assert(flavors.getStockFlavor(x86_64) == deps.parseFlavor(flavors.stockFlavors['1#x86_64']))

        x86_64 = deps.ThawFlavor('1#x86_64|1#x86:i486:i586:i686:~!sse2')
        assert(flavors.getStockFlavor(x86_64) == deps.parseFlavor(flavors.stockFlavors['1#x86_64']))

    def testGetStockFlavorPaths(self):
        # make sure that pathSearchOrder contains all of the flavors in stockFlavorPaths
        assert(set(flavors.pathSearchOrder) == set(flavors.stockFlavorPaths.keys()))

        x86 = deps.ThawFlavor('1#x86:cmov:i486:i586:i686:~!mmx:~!sse2')
        x86_64 = deps.ThawFlavor('1#x86:i486:i586:i686:~!sse2|1#x86_64')

        x86Path = [deps.parseFlavor(x) for x in flavors.stockFlavorPaths['1#x86']]
        x86_64Path = [deps.parseFlavor(x) for x in flavors.stockFlavorPaths['1#x86_64']]

        assert([x.freeze() for x in flavors.getStockFlavorPath(x86)] == [x.freeze() for x in x86Path])
        assert([x.freeze() for x in flavors.getStockFlavorPath(x86_64)] == [x.freeze() for x in x86_64Path])


class FixturedHelpersTest(fixtures.FixturedUnitTest):
    @fixtures.fixture('Full')
    def testIndeces(self, db, data):
        # the tables have already been loaded. doing an independent load in
        # this manner will uncover table index dicts with a name mismatch
        db.loadSchema()
        tableObjs = server.getTables(db, self.cfg)


if __name__ == "__main__":
    testsuite.main()

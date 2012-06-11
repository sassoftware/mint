#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#

import testsuite
import unittest
testsuite.setup()

import kid
import logging
import os
import sys
import tempfile

from mint_test import mint_rephelp
from mint import config
from mint.lib import copyutils
from mint.lib import scriptlibrary
from mint import templates
from mint import flavors
from mint.helperfuncs import *
from mint.client import timeDelta
from mint.userlevels import myProjectCompare
from mint.web import templatesupport

from conary import versions
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

class HelperFunctionsTest(mint_rephelp.MintRepositoryHelper, unittest.TestCase):
    def testMyProjectCompare(self):
        if not isinstance(myProjectCompare(('not tested', 1),
                                           ('ignored', 0)), int):
            self.fail("myProjectCompare did not return an int")
        if not isinstance(myProjectCompare(('not tested', 1L),
                                           ('ignored', 0L)), int):
            self.fail("myProjectCompare did not return an int")

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
        raise testsuite.SkipTestException("This plugin messes up the kid importer for the rapa tests, skipping for now")
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

    # Unfriendly because javascript is installed to a different location
    # when testing against installed rbuilder; this is more useful on
    # the developer's system anyway.
    @testsuite.context("unfriendly")
    def testJavascript(self):
        # whizzyupload.js was validated with jslint
        whiteList = ['json.js', 'whizzyupload.js', 'swf_deeplink_history.js', 'history.js', 'iClouds.js', 'AC_OETags.js']
        scriptPath = os.path.join(os.path.split(os.path.split(\
            os.path.realpath(__file__))[0])[0], 'mint', 'web', 'content',
                                   'javascript')
        for library in \
                [x for x in os.listdir(scriptPath) if x.endswith('.js') and x not in whiteList and not x.startswith('jquery')]:
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
                if line and line[-1] not in [';', '{', '}', '(', '[', '+']:
                    broken = True
                    for tok in ('if', 'else', 'for', 'while', 'case',
                                'default'):
                        if line.startswith(tok):
                            broken = False
                    if broken:
                        import epdb
                        epdb.st()
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

    def testUnwritableScriptLog(self):
        '''
        Check that the script logger deals with an unwritable log by
        not opening the file logger.

        @tests: RBL-3042
        '''

        def mockSetup(path):
            scriptlibrary._scriptLogger.setup = True
            self.failUnlessEqual(path, None)
            class MockLogger(object):
                def warning(xself, msg, *args):
                    pass
            return MockLogger()

        _setup = scriptlibrary.setupScriptLogger
        try:
            scriptlibrary.setupScriptLogger = mockSetup

            fd, fn = tempfile.mkstemp()
            os.chmod(fn, 0)
            os.close(fd)
            script = scriptlibrary.GenericScript()
            script.logPath = fn
            script.resetLogging()
        finally:
            scriptlibrary.setupScriptLogger = _setup

    def testMissingScriptLogFile(self):
        '''
        Check that a writable log directory but no log file still
        results in a log being opened.

        @tests: RBL-3042
        '''

        logdir = tempfile.mkdtemp()
        logfile = os.path.join(logdir, "foo.log")

        calls = [0]
        def mockSetup(path):
            scriptlibrary._scriptLogger.setup = True
            if not calls[0]:
                # First call is implicit and has no logfile
                self.failUnlessEqual(path, None)
            else:
                # Second call is by us
                self.failUnlessEqual(path, logfile)
            calls[0] += 1
            return True

        _setup = scriptlibrary.setupScriptLogger
        try:
            scriptlibrary.setupScriptLogger = mockSetup
            script = scriptlibrary.GenericScript()
            script.logPath = logfile
            script.resetLogging()
            self.failUnless(os.path.exists(logfile),
                "log file was not opened")
            # check that mockSetup got called twice
            self.failUnlessEqual(calls, [2],
                "script log was not re-opened")
        finally:
            scriptlibrary.setupScriptLogger = _setup
            util.rmtree(logdir)

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
            if not (os.stat(os.path.join(curdir, modl))[0] & 0100):
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

    def testCopyTree(self):
        # test copying tree with different syntaxes
        d = tempfile.mkdtemp()
        subdir = os.sep.join((d, 'subdir'))
        os.mkdir(subdir)
        fn = os.sep.join((subdir, 'hello'))
        f = open(fn, 'w')
        f.write('hello')
        d2 = tempfile.mkdtemp()
        subdir2 = os.sep.join((d2, 'subdir'))
        fn2 = os.sep.join((subdir2, 'hello'))
        copyutils.copytree(subdir, d2, fileowner = (os.getuid(), os.getgid()))
        assert(os.path.isdir(subdir2) and os.path.exists(fn2))
        util.rmtree(subdir2)
        copyutils.copytree(subdir + '/', d2)
        assert(os.path.isdir(subdir2) and os.path.exists(fn2))

        copyutils.copytree(subdir + '/hello', d2)
        assert(os.path.isdir(subdir2) and os.path.exists(fn2))
        util.rmtree(d)

    def testDatabaseTimestampFunctions(self):
        x = time.time()
        y = fromDatabaseTimestamp(toDatabaseTimestamp(x))
        self.assertEqual(int(x), int(y), "failed normal case")

        x = time.time() + 900
        y = fromDatabaseTimestamp(toDatabaseTimestamp(x, offset=900)) - 900
        self.assertEqual(int(x), int(y), "failed with offset")

        x = time.time()
        y = fromDatabaseTimestamp(str(toDatabaseTimestamp(x)))
        self.assertEqual(int(x), int(y), "failed using string")

        x = time.time()
        y = fromDatabaseTimestamp(unicode(toDatabaseTimestamp(x)))
        self.assertEqual(int(x), int(y), "failed using unicode")

        self.assertRaises(ValueError, fromDatabaseTimestamp, '34842afjk')
        self.assertRaises(ValueError, fromDatabaseTimestamp, [])

    def testGeneratePassword(self):
        p1 = genPassword(32)
        self.assertTrue(len(p1) == 32)

    def testGetBuildIdFromUuid(self):
        buildId = 8
        count = 1
        uuid = '%s.%s-build-%d-%d' %('foo', 'bar.com', buildId, count)
        newBuildId = getBuildIdFromUuid(uuid)
        self.assertTrue(newBuildId == buildId)

    def testCollateDictByKeyPrefix(self):
                
        class KlassToStr(object):
            """ Fake class just used to test coercion """
            def __init__(self, s):
                self.s = s
            def __str__(self):
                return self.s
            
        dict_typical = {
                 'prefix1-1-foo':       'foovalue1',
                 'prefix1-1-bar':       'barvalue1',
                 'prefix1-1-baz':       'bazvalue1',
                 'prefix1-1-oh-noes':   'oh-noes-value1',
                 'prefix1-2-foo':       'foovalue2',
                 'prefix1-2-bar':       'barvalue2',
                 'prefix1-2-baz':       'bazvalue2',
                 'prefix1-2-oh-noes':   'oh-noes-value2',
                 'otherprefix-1-quux':  'quuxvalue1',
                 'otherprefix-2-quux':  'quuxvalue2',
                 'otherprefix-3-quux':  'quuxvalue3',
                 'nonconformist':       'fightthapowa!',
                 'klass-1-wargh':       KlassToStr('mine'),
                 'klass-2-wargh':       KlassToStr('yours'),
                 'bad-prefix-1':        'ignored',
                 '-bad-prefix-2':       'ignored',
                 '--':                  'ignored',
                 '-':                   'ignored',
                 '':                    'ignored',
                 }
                
        collatedDict = collateDictByKeyPrefix(dict_typical, False)
        coercedCollatedDict = collateDictByKeyPrefix(dict_typical, True)
        collatedEmptyDict = collateDictByKeyPrefix({})
        
        self.failUnlessEqual(len(collatedDict.get('prefix1')), 2)
        
        self.failUnlessEqual(len(collatedDict.get('otherprefix')), 3)
        
        self.failIf('nonconformist' in collatedDict,
                    "Non-conforming keys should not be included in collation")

        self.failUnlessEqual(collatedEmptyDict, {})
        
        self.failUnlessEqual([k for k in collatedDict if k.find('-') >= 0], [],
                "Key with hyphens should not be let through")

        self.failUnlessEqual([k for k in collatedDict if k.find('bad') >= 0], [],
                "Bad prefix allowed")

        self.failUnlessEqual(len([i['oh-noes'] for i in collatedDict.get('prefix1')]), 2)

        klassesNonCoerced = collatedDict.get('klass')
        for i in klassesNonCoerced:
            for k, v in i.iteritems():
                self.failUnlessEqual(k, 'wargh', 'Unexpected key %s' % k)
                self.failUnless(isinstance(v, KlassToStr),
                                'Should be class value')
            
        klassesCoerced = coercedCollatedDict.get('klass')
        for i in klassesCoerced:
            for k, v in i.iteritems():
                self.failUnlessEqual(k, 'wargh', 'Unexpected key %s' % k)
                self.failUnless(isinstance(v, str),
                                'Should be str value')
                
    def testGetBuildDefsAvaliableBuildTypes(self):
        client, userId = self.quickMintUser('foouser','foopass')
        buildTypes = getBuildDefsAvaliableBuildTypes(
                         client.getAvailableBuildTypes())
        
        # make sure imageless is not in there
        self.assertTrue(buildtypes.IMAGELESS not in buildTypes)
        
    def testValidateNamespace(self):
        """
        Test valid/invalid config namespace values
        """
        self.assertTrue(validateNamespace("rpl"))
        self.assertTrue(validateNamespace("foo2-*&^%$#!"))
        
        # invalid should return string text explainign what is wrong
        text = validateNamespace("rpl:blah")
        self.assertTrue(isinstance(text, str))
        
        # invalid should return string text explainign what is wrong
        text = validateNamespace("rpl@blah")
        self.assertTrue(isinstance(text, str))
        

    def testProductDefinition(self):
        prd = sanitizeProductDefinition('foo', '', 'foo', 'rpath.local',
                'foo', '1', '', 'foo')
        self.failUnless(prd.platform.containerTemplates)
        self.failUnless(prd.platform.architectures)
        self.failUnless(prd.platform.flavorSets)
        self.failUnless(prd.platform.buildTemplates)
        self.failUnless(prd.platform.baseFlavor)
        self.failIf(prd.baseFlavor)

        from rpath_proddef import api1 as proddef

        plt = proddef.PlatformDefinition()
        plt.addContainerTemplate(prd.imageType('installableIsoImage'))
        prd.platform = plt

        prd2 = sanitizeProductDefinition('foo', '', 'foo', 'rpath.local',
                'foo', '1', '', 'foo', productDefinition = prd)

        self.failUnless(prd2.platform.containerTemplates)
        self.failIf(prd2.platform.architectures)
        self.failIf(prd2.platform.flavorSets)
        self.failIf(prd2.platform.buildTemplates)
        self.failIf(prd2.platform.baseFlavor)
        self.failIf(prd2.baseFlavor)

    def testProdDefNoPlatDef(self):
        from rpath_proddef import api1 as proddef
        prd = proddef.ProductDefinition()
        # ensure we don't have a platform definition at all
        prd.platform = None
        addDefaultPlatformToProductDefinition(prd)
        self.failUnless(hasattr(prd, 'platform'))

    def testProdDefPredefined(self):
        from rpath_proddef import api1 as proddef
        # a single definition of flavorSet, architecture, containerTemplate, or
        # buildTemplate should be enough to stop the defaults
        prd = proddef.ProductDefinition()
        prd.addFlavorSet('test', 'test', 'test')
        addDefaultPlatformToProductDefinition(prd)
        self.failIf(prd.platform.containerTemplates)
        self.failIf(prd.platform.architectures)
        self.failIf(prd.platform.flavorSets)
        self.failIf(prd.platform.buildTemplates)

        prd = proddef.ProductDefinition()
        prd.addArchitecture('test', 'test', 'test')
        addDefaultPlatformToProductDefinition(prd)
        self.failIf(prd.platform.containerTemplates)
        self.failIf(prd.platform.architectures)
        self.failIf(prd.platform.flavorSets)
        self.failIf(prd.platform.buildTemplates)

        prd = proddef.ProductDefinition()
        prd.addContainerTemplate(prd.imageType('installableIsoImage'))
        addDefaultPlatformToProductDefinition(prd)
        self.failIf(prd.platform.containerTemplates)
        self.failIf(prd.platform.architectures)
        self.failIf(prd.platform.flavorSets)
        self.failIf(prd.platform.buildTemplates)

        prd = proddef.ProductDefinition()
        prd.addBuildTemplate(name = "ami_large",
                displayName = "EC2 AMI Large/Huge", architectureRef = "x86_64",
                containerTemplateRef = "amiImage", flavorSetRef = "ami")
        addDefaultPlatformToProductDefinition(prd)
        self.failIf(prd.platform.containerTemplates)
        self.failIf(prd.platform.architectures)
        self.failIf(prd.platform.flavorSets)
        self.failIf(prd.platform.buildTemplates)


    def testUrlSplitUnsplit(self):
        tests = [
            (("http", None, None, "localhost", None, "/path", "q", "f"),
              "http://localhost/path?q#f"),
            (("http", 'u', 'p', "localhost", None, "/path", None, None),
              "http://u:p@localhost/path"),
            (("http", 'u', 'p', "localhost", 103, "/path", None, None),
              "http://u:p@localhost:103/path"),
            (("http", 'u', 'p a s s', "localhost", 103, "/path", None, None),
              "http://u:p%20a%20s%20s@localhost:103/path"),
            # According to RFC2617, the password can be any character,
            # including newline. However, urllib's regex will stop at the new
            # line.
            #(("http", 'u', 'p\nq', "localhost", 103, "/path", None, None),
            #  "http://u:p%0Aq@localhost:103/path"),
            (("http", 'u\tv', 'p\tq', "localhost", 103, "/path", None, None),
              "http://u%09v:p%09q@localhost:103/path"),
        ]
        for tup, url in tests:
            nurl = urlUnsplit(tup)
            self.failUnlessEqual(nurl, url)
            self.failUnlessEqual(urlSplit(url), tup)

        # One-way tests
        tests = [
            (("http", None, None, "localhost", "10", "/path", "", ""),
              "http://localhost:10/path"),
        ]
        for tup, url in tests:
            nurl = urlUnsplit(tup)
            self.failUnlessEqual(nurl, url)

        # One-way tests
        tests = [
            (("http", None, None, "localhost", None, "/path", "q", "f"),
              "http://localhost/path?q#f"),
        ]
        for tup, url in tests:
            nurl = urlUnsplit(tup)
            self.failUnlessEqual(urlSplit(url), tup)

if __name__ == "__main__":
    testsuite.main()

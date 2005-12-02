#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2004 rpath, Inc.
#

import grp
import sys
import os
import os.path
import pwd
import re
import tempfile
import types
import unittest

from conary.lib import util, log

archivePath = None
testPath = None

#from pychecker import checker

class LogFilter:
    def __init__(self):
        self.records = []
        self.ignorelist = []

    def clear(self):
        self.records = []
        self.ignorelist = []
        log.logger.removeFilter(self)

    def filter(self, record):
        text = log.formatter.format(record)
        for regex in self.ignorelist:
            if regex.match(text):
                return False
        self.records.append(text)
        return False

    def ignore(self, regexp):
        self.ignorelist.append(re.compile(regexp))

    def add(self):
        log.logger.addFilter(self)

    def remove(self):
        log.logger.removeFilter(self)

    def compareWithOrder(self, records):
        """
        compares stored log messages against a sequence of messages and
        resets the filter
        """
	if self.records == None or self.records == []:
	    if records:
		raise AssertionError, "unexpected log messages"
	    return
        if type(records) is str:
            records = (records,)

	if len(records) != len(self.records):
	    raise AssertionError, "expected log message count does not match"
	    
        for num, record in enumerate(records):
            if self.records[num] != record:
                raise AssertionError, "expected log messages do not match: '%s' != '%s'" %(self.records[num], record)
        self.records = []

    def compare(self, records):
        """
        compares stored log messages against a sequence of messages and
        resets the filter.  order does not matter.
        """
	if self.records == None or self.records == []:
	    if records:
		raise AssertionError, "unexpected log messages"
	    return
        if type(records) is str:
            records = (records,)

	if len(records) != len(self.records):
	    raise AssertionError, "expected log message count does not match"
	    
        for record in records:
            if not record in self.records:
                raise AssertionError, "expected log message not found: '%s'" %record

        for record in self.records:
            if not record in records:
                raise AssertionError, "unexpected log message not found: '%s'" %record

        self.records = []

conaryDir = None

def setup():
    global testPath
    global archivePath

    if not os.environ.has_key('CONARY_PATH'):
	print "please set CONARY_PATH"
	sys.exit(1)
    if not os.environ.has_key('MINT_PATH'):
        print "please set MINT_PATH"
        sys.exit(1)
    sys.path.insert(0, os.environ['CONARY_PATH'])
    sys.path.insert(0, os.environ['MINT_PATH'])
    sys.path.insert(1, os.path.join(os.environ['CONARY_PATH'], 'conary/server'))
    if 'PYTHONPATH' in os.environ:
        os.environ['PYTHONPATH'] = os.pathsep.join((os.environ['CONARY_PATH'],
                                                    os.environ['PYTHONPATH']))
    else:
        os.environ['PYTHONPATH'] = os.environ['CONARY_PATH']

    if isIndividual():
        serverDir = '/tmp/conary-server'
        if os.path.exists(serverDir) and not os.path.access(serverDir, os.W_OK):
            serverDir = serverDir + '-' + pwd.getpwuid(os.getuid())[0]
        os.environ['SERVER_FILE_PATH'] = serverDir

    invokedAs = sys.argv[0]
    if invokedAs.find("/") != -1:
        if invokedAs[0] != "/":
            invokedAs = os.getcwd() + "/" + invokedAs
        path = os.path.dirname(invokedAs)
    else:
        path = os.getcwd()

    testPath = os.path.realpath(path)
    # find the top of the test directory in the full path - this
    # sets the right test path even when testsuite.setup() is called
    # from a testcase in a subdirectory of the testPath
    if sys.modules.has_key('testsuite'):
        testPath = os.path.join(testPath, os.path.dirname(sys.modules['testsuite'].__file__))
    archivePath = testPath + '/' + "archive"
    parent = os.path.dirname(testPath)

    global conaryDir, mintDir
    conaryDir = os.environ['CONARY_PATH']
    mintDir = os.environ['MINT_PATH']
    if parent not in sys.path:
	sys.path.append(parent)

    from conary.lib import util
    sys.excepthook = util.genExcepthook(True)

    return path

class Loader(unittest.TestLoader):
    suiteClass = unittest.TestSuite

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module"""
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, (type, types.ClassType)) and
                issubclass(obj, unittest.TestCase)):
                tests.append(self.loadTestsFromTestCase(obj))
            if (isinstance(obj, unittest.TestSuite)):
                tests.append(obj)
        return self.suiteClass(tests)

    def loadTestsFromName(self, name, module=None):
        # test to make sure we can load what we're trying to load
        # since we can generate a better error message up front.
        if not module:
            try:
                __import__(name)
            except ImportError, e:
                print 'unable to import module %s: %s' %(name, e)
                raise
        try:
            f = unittest.TestLoader.loadTestsFromName(self, name,
                                                      module=module)
            if isinstance(f, unittest.TestSuite) and not f._tests:
                raise RuntimeError, 'no tests in %s' %name
            return f
        except AttributeError:
            # try to find a method of a test suite class that matches
            # the thing given
            for objname in dir(module):
                try:
                    newname = '.'.join((objname, name))
                    return unittest.TestLoader.loadTestsFromName(self, newname,
                                                                 module=module)
                except AttributeError:
                    pass
                except ImportError, e:
                    print 'unable to import tests from %s: %s' %(newname, e)
                    raise
        except ImportError, e:
            print 'unable to import tests from %s: %s' %(name, e)
            raise
        raise AttributeError

class TestCase(unittest.TestCase):
    def setUp(self):
        self._logLevel = log.getVerbosity()

    def tearDown(self):
        log.setVerbosity(self._logLevel)

    def captureOutput(self, fn, *args, **namedArgs):
	sys.stdout.flush()
	(fd, file) = tempfile.mkstemp()
	os.unlink(file)
	stdout = os.dup(sys.stdout.fileno())
	os.dup2(fd, sys.stdout.fileno())
	try:
	    fnRc = fn(*args, **namedArgs)
	    sys.stdout.flush()
	except:
	    os.dup2(stdout, sys.stdout.fileno())
	    os.close(fd)
	    raise

	os.dup2(stdout, sys.stdout.fileno())

	os.lseek(fd, 0, 0)
	str = ""
	rc = os.read(fd, 1024)
	while (rc):
	    str += rc
	    rc = os.read(fd, 1024)

	os.close(fd)

	return (fnRc, str)

    def logCheck(self, fn, args, log, kwargs={}):
	self.logFilter.add()
	rc = fn(*args, **kwargs)
	try:
	    self.logFilter.compare(log)
	finally:
	    self.logFilter.remove()
	return rc

    def __init__(self, methodName):
	unittest.TestCase.__init__(self, methodName)
        self.logFilter = LogFilter()
        self.owner = pwd.getpwuid(os.getuid())[0]
        self.group = grp.getgrgid(os.getgid())[0]

	global conaryDir, mintDir
	self.conaryDir = conaryDir
        self.mintDir = mintDir

    def mimicRoot(self):
	self.oldgetuid = os.getuid
	self.oldmknod = os.mknod
	self.oldlchown = os.lchown
	self.oldchown = os.chown
	self.oldchmod = os.chmod
	self.oldchroot = os.chroot
	self.oldexecl = os.execl
	self.oldutime = os.utime
	os.getuid = lambda : 0
	os.mknod = self.ourMknod
	os.lchown = self.ourChown
	os.chown = self.ourChown
	os.chmod = self.ourChmod
	os.chroot = self.ourChroot
	os.execl = self.ourExecl
	os.utime = lambda x, y: 0
	self.thisRoot = ''
	self.chownLog = []
        self.chmodLog = []
	self.mknodLog = []

    def ourChroot(self, *args):
	self.thisRoot = os.sep.join((self.thisRoot, args[0]))

    def ourExecl(self, *args):
	args = list(args)
	args[0:1] = [os.sep.join((self.thisRoot, args[0]))]
	self.oldexecl(*args)

    def ourChown(self, *args):
	self.chownLog.append(args)

    def ourMknod(self, *args):
	self.mknodLog.append(args)

    def ourChmod(self, *args):
	# we cannot chmod a file that doesn't exist (like a device node)
	# try the chmod for files that do exist
        self.chmodLog.append(args)
	try:
	    self.oldchmod(*args)
	except:
	    pass

    def realRoot(self):
	os.getuid = self.oldgetuid
	os.mknod = self.oldmknod
	os.lchown = self.oldlchown
	os.chown = self.oldchown
	os.chmod = self.oldchmod
	os.chroot = self.oldchroot
	os.execl = self.oldexecl
	os.utime = self.oldutime
	self.chownLog = []

def main(*args, **keywords):
    sys.excepthook = util.genExcepthook(True)

    global _individual
    _individual = True
    loader = Loader()

    verbosity=1
    if '-v' in sys.argv:
        verbosity=2
        sys.argv.remove('-v')
        
    if '--debug' in sys.argv:
        sys.argv.remove('--debug')
        runner = DebugTestRunner(verbosity=verbosity)
    else:
        runner = unittest.TextTestRunner(verbosity=verbosity)
        
    unittest.main(testRunner=runner, testLoader=loader, *args, **keywords)

class DebugTextResult(unittest._TextTestResult):
    def addError(self, test, err):
        raise err[0], err[1], err[2]

    def addFailure(self, test, err):
        raise err[0], err[1], err[2]

class DebugTestRunner(unittest.TextTestRunner):
    def _makeResult(self):
        return DebugTextResult(self.stream, self.descriptions, self.verbosity)

_individual = False

def isIndividual():
    global _individual
    return _individual

if __name__ == '__main__':
    tests = []
    topdir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    topdir = os.path.normpath(topdir)
    cwd = os.getcwd()
    sys.path.append(topdir)
    if cwd != topdir:
        sys.path.append(cwd)
    setup()

    sys.excepthook = util.genExcepthook(True)

    debug = False
    if '--debug' in sys.argv:
	debug = True
	sys.argv.remove('--debug')

    verbosity = 1
    if '-v' in sys.argv:
        verbosity = 2
        sys.argv.remove('-v')

    profiling = False
    if '--profile' in sys.argv:
	import hotshot
	prof = hotshot.Profile('conary.prof')
	prof.start()
        profiling = True
	sys.argv.remove('--profile')

    if sys.argv[1:]:
	tests = []
	for s in sys.argv[1:]:
	    # strip the .py
            if s.endswith('.py'):
                s = s[:-3]
            if topdir != cwd:
                s = '%s.%s' %(cwd[len(topdir) + 1:].replace('/', '.'), s)
            tests.append(s)
    else:
	for (dirpath, dirnames, filenames) in os.walk(topdir):
	    for f in filenames:
		if f.endswith('test.py') and not f.startswith('.'):
		    # turn any subdir into a dotted module string
		    d = dirpath[len(topdir) + 1:].replace('/', '.')
		    if d:
			# if there's a subdir, add a . to delineate
			d += '.'
		    # strip off .py
		    tests.append(d + f[:-3])

    loader = Loader()
    suite = unittest.TestSuite()

    for test in tests:
        testcase = loader.loadTestsFromName(test)
        suite.addTest(testcase)

    if debug:
        cls = DebugTestRunner
    else:
        cls = unittest.TextTestRunner

    runner = cls(verbosity=verbosity)
    runner.run(suite)

    if profiling:
        prof.stop()

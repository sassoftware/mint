#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2004 rpath, Inc.
#

import bdb
import cPickle
import grp
import sys
import os
import os.path
import pwd
import socket
import re
import tempfile
import time
import types
import unittest

archivePath = None
testPath = None

#from pychecker import checker

portstart = 60000
def findPorts(num = 1):
    foundport = False
    global portstart
    ports = []
    for port in xrange(portstart, portstart + 100):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(('localhost', port))
            s.close()
        except:
            pass
        else:
            ports.append(port)
            if len(ports) == num:
                portstart = max(ports) + 1
                return ports

    if not foundport:
        raise socket.error, "Cannot find open port to run server on"

def context(*contexts):
    def deco(func):
        # no wrapper is needed, nor usable.
        if '_contexts' in func.__dict__:
            func._contexts.extend(contexts)
        else:
            func._contexts = list(contexts)
        return func
    return deco

class LogFilter:
    def __init__(self):
        self.records = []
        self.ignorelist = []

    def clear(self):
        from conary.lib import log
        self.records = []
        self.ignorelist = []
        log.logger.removeFilter(self)

    def filter(self, record):
        from conary.lib import log
        text = log.formatter.format(record)
        for regex in self.ignorelist:
            if regex.match(text):
                return False
        self.records.append(text)
        return False

    def ignore(self, regexp):
        self.ignorelist.append(re.compile(regexp))

    def add(self):
        from conary.lib import log
        log.logger.addFilter(self)

    def remove(self):
        from conary.lib import log
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
_setupPath = None
def setup():
    global _setupPath
    if _setupPath:
        return _setupPath
    global testPath
    global archivePath

    if not os.environ.has_key('CONARY_PATH') or not os.environ.has_key('MINT_PATH'):
	print "please set CONARY_PATH and MINT_PATH"
	sys.exit(1)
    paths = (os.environ['MINT_PATH'], os.environ['MINT_PATH'] + '/test',
             os.environ['CONARY_PATH'],
             '/'.join(os.environ['CONARY_PATH'].split('/')[:-1]) \
             + '/conary-test')
    pythonPath = os.getenv('PYTHONPATH') or ""
    for p in reversed(paths):
        if p in sys.path:
            sys.path.remove(p)
        sys.path.insert(0, p)
    for p in paths:
        if p not in pythonPath:
            pythonPath = os.pathsep.join((pythonPath, p))
    os.environ['PYTHONPATH'] = pythonPath

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

    global conaryDir
    conaryDir = os.environ['CONARY_PATH']

    from conary.lib import util
    sys.excepthook = util.genExcepthook(True)

    # import debugger now that we have the path for it
    global debugger
    from conary.lib import debugger

    _setupPath = path
    return path

class Loader(unittest.TestLoader):
    suiteClass = unittest.TestSuite

    def _filterTests(self, tests):
        if not self.context:
            return
        for testCase in tests._tests[:]:
            try:
                method = testCase.__getattribute__( \
                    testCase._TestCase__testMethodName)
                contexts = method._contexts
                if self.context not in contexts:
                    tests._tests.remove(testCase)
            except AttributeError:
                tests._tests.remove(testCase)

    def loadTestsFromModule(self, module):
        """Return a suite of all tests cases contained in the given module"""
        tests = []
        for name in dir(module):
            obj = getattr(module, name)
            if (isinstance(obj, (type, types.ClassType)) and
                issubclass(obj, unittest.TestCase)):
                loadedTests = self.loadTestsFromTestCase(obj)
                self._filterTests(loadedTests)
                tests.append(loadedTests)
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
                    # context shouldn't apply. test cases were named directly
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

    def __init__(self, context = None):
        unittest.TestLoader.__init__(self)
        self.context = context

class TestCase(unittest.TestCase):

    def setUp(self):
        from conary.lib import log
        self._logLevel = log.getVerbosity()

    def tearDown(self):
        from conary.lib import log
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

	global conaryDir
	self.conaryDir = conaryDir

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

class TestTimer(object):
    def __init__(self, file, testSuite):
        self.startAll = time.time()
        if os.path.exists(file):
            try:
                self.times = cPickle.load(open(file))
            except Exception, msg:
                print "error loading test times:", msg
                self.times = {}
        else:
            self.times = {}
        self.file = file

        self.toRun = set()
        testSuites = [testSuite]
        while testSuites:
            testSuite = testSuites.pop()
            if not isinstance(testSuite, unittest.TestCase):
                testSuites.extend(x for x in testSuite) 
            else:
                self.toRun.add(testSuite.id())
                
    def startTest(self, test):
        self.testStart = time.time()
        self.testId = test.id()

    def stopTest(self, test):
        id = self.testId
        self.toRun.discard(id)

    def testPassed(self):
        id = self.testId
        thisTime = time.time() - self.testStart
        avg, times = self.times.get(id, [0, 0])
        avg = ((avg * times) + thisTime) / (times + 1.0)
        times = min(times+1, 3)
        self.times[id] = [avg, times]
        self.store(self.file)

    def estimate(self):
        left =  sum(self.times.get(x, [1])[0] for x in self.toRun)
        passed = time.time() - self.startAll
        return  passed, passed + left

    def store(self, file):
        cPickle.dump(self.times, open(file, 'w'))


class SkipTestException(Exception):
    pass

class SkipTestResultMixin:
    def __init__(self):
        self.skipped = []

    def checkForSkipException(self, test, err):
        # because of the reloading of modules that occurs when
        # running multiple tests, no guarantee about the relation of
        # this SkipTestException class to the one run in the 
        # actual test can be made, so just check names
        if err[0].__name__ == 'SkipTestException':
            self.addSkipped(test, err)
            return True

    def addSkipped(self, test, err):
        self.skipped.append(test)

    def __repr__(self):
        return ("<%s run=%i errors=%i failures=%i skipped=%i>" %
                (unittest._strclass(self.__class__), self.testsRun,
                 len(self.errors), len(self.failures),
                 len(self.skipped)))


class TestCallback:

    def _message(self, msg):
        self.out.write("\r")
        self.out.write(msg)
        if len(msg) < self.last:
            i = self.last - len(msg)
            self.out.write(" " * i + "\b" * i)
        self.out.flush()
        self.last = len(msg)

    def __del__(self):
        if self.last:
            self._message("")
            print "\r",
            self.out.flush()

    def clear(self):
        self._message("")
        print "\r",

    def __init__(self, f = sys.stdout):
        self.last = 0
        self.out = f

    def totals(self, run, passed, failed, errored, skipped, total, 
                timePassed, estTotal, test=None):
        totals = (failed +  errored, skipped, timePassed / 60, 
                  timePassed % 60, estTotal / 60, estTotal % 60, run, total)
        msg = 'Fail: %s Skip: %s - %0d:%02d/%0d:%02d - %s/%s' % totals

        if test:
            # append end of test to message
            id = test.id()
            cutoff = max((len(id) + len(msg)) - 76, 0)
            msg = msg + ' - ' + id[cutoff:]

        self._message(msg)


class SkipTestTextResult(unittest._TextTestResult, SkipTestResultMixin):

    def __init__(self, *args, **kw):
        test = kw.pop('test')
        self.debug = kw.pop('debug', False)
        self.useCallback = kw.pop('useCallback', True)
        self.passedTests = 0
        self.failedTests = 0
        self.erroredTests = 0
        self.skippedTests = 0
        self.total = test.countTestCases()
        self.callback = TestCallback()
        unittest._TextTestResult.__init__(self, *args, **kw)
        SkipTestResultMixin.__init__(self)
        self.timer = TestTimer('.times', test)

    def addSkipped(self, test, err):
        self.skippedTests += 1
        SkipTestResultMixin.addSkipped(self, test, err)
        if self.useCallback:
            self.callback.clear()
            print 'SKIPPED:', test.id()

    def addError(self, test, err):
        if isinstance(err[1], bdb.BdbQuit):
            raise KeyboardInterrupt

        if self.checkForSkipException(test, err):
            return

        if not self.useCallback:
            unittest._TextTestResult.addError(self, test, err)
        else:
            unittest.TestResult.addError(self, test, err)
            self.callback.clear()
            desc = self._exc_info_to_string(err, test)
            self.printErrorList('ERROR', [(test, desc)])

        if self.debug:
            debugger.post_mortem(err[2], err[1], err[0])

        self.erroredTests += 1


    def addFailure(self, test, err):
        if not self.useCallback:
            unittest._TextTestResult.addFailure(self, test, err)
        else:
            unittest.TestResult.addFailure(self, test, err)
            self.callback.clear()
            desc = self._exc_info_to_string(err, test)
            self.printErrorList('FAILURE', [(test, desc)])

        if self.debug:
            debugger.post_mortem(err[2], err[1], err[0])

        self.failedTests += 1

    def addSuccess(self, test):
        self.timer.testPassed()
        self.passedTests += 1

        if not self.useCallback:
            unittest._TextTestResult.addSuccess(self, test)

    def startTest(self, test):
        unittest._TextTestResult.startTest(self, test)
        self.timer.startTest(test)
        self.printTotals(test)

    def stopTest(self, test):
        unittest._TextTestResult.stopTest(self, test)
        self.timer.stopTest(test)
        self.printTotals()


    def printTotals(self, test=None):
        if self.useCallback:
            timePassed, totalTime = self.timer.estimate()
            self.callback.totals(self.testsRun, self.passedTests,
                                 self.failedTests,
                                 self.erroredTests, self.skippedTests, 
                                 self.total, timePassed, totalTime, test)


class DebugTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        self.debug = kwargs.pop('debug', False)
        self.useCallback = kwargs.pop('useCallback', False)
        unittest.TextTestRunner.__init__(self, *args, **kwargs)

    def run(self, test):
        self.test = test
        result = self._makeResult()
        startTime = time.time()
        test(result)
        stopTime = time.time()
        timeTaken = stopTime - startTime
        self.stream.writeln('\n' + result.separator2)
        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        return result

    def _makeResult(self):
        return SkipTestTextResult(self.stream, self.descriptions,
                                  self.verbosity, test=self.test, 
                                  debug=self.debug,
                                  useCallback=self.useCallback)


_individual = False

def isIndividual():
    global _individual
    return _individual


def main(*args, **keywords):
    from conary.lib import util
    sys.excepthook = util.genExcepthook(True)

    global _individual
    _individual = True

    context = None
    if '--context' in sys.argv:
        argLoc = sys.argv.index('--context')
        context = sys.argv[argLoc + 1]
        sys.argv.remove('--context')
        sys.argv.pop(argLoc)

    loader = Loader(context = context)

    verbosity=1
    dots = False

    if '-v' in sys.argv:
        verbosity=2
        sys.argv.remove('-v')
        dots = True

    if '--dots' in sys.argv:
        sys.argv.remove('--dots')
        dots = True

        
    if '--debug' in sys.argv:
        debug = True
        sys.argv.remove('--debug')
    else:
        debug=False

    runner = DebugTestRunner(verbosity=verbosity, debug=debug, 
                             useCallback=not dots)
        
    unittest.main(testRunner=runner, testLoader=loader, *args, **keywords)


if __name__ == '__main__':
    tests = []
    topdir = os.path.join(os.getcwd(), os.path.dirname(sys.argv[0]))
    topdir = os.path.normpath(topdir)
    cwd = os.getcwd()
    if topdir not in sys.path:
        sys.path.insert(0, topdir)
    if cwd != topdir and cwd not in sys.path:
        sys.path.insert(0, cwd)
    setup()

    from conary.lib import util
    from conary.lib import debugger
    sys.excepthook = util.genExcepthook(True)

    debug = False
    dots = False
    if '--debug' in sys.argv:
	debug = True
	sys.argv.remove('--debug')

    verbosity = 1
    if '-v' in sys.argv:
        verbosity = 2
        sys.argv.remove('-v')
        dots = True

    if '--dots' in sys.argv:
        dots = True
        sys.argv.remove('--dots')

    profiling = False
    if '--profile' in sys.argv:
	import hotshot
	prof = hotshot.Profile('conary.prof')
	prof.start()
        profiling = True
	sys.argv.remove('--profile')

    context = None
    if '--context' in sys.argv:
        argLoc = sys.argv.index('--context')
        context = sys.argv[argLoc + 1]
        sys.argv.remove('--context')
        sys.argv.pop(argLoc)

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

    loader = Loader(context = context)
    suite = unittest.TestSuite()

    for test in tests:
        testcase = loader.loadTestsFromName(test)
        suite.addTest(testcase)

    runner = DebugTestRunner(verbosity=verbosity, debug=debug, 
                             useCallback=not dots)
    runner.run(suite)

    if profiling:
        prof.stop()

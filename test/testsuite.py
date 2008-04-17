#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2005-2008 rPath, Inc.
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
import __builtin__

testPath = None
archivePath = None

#from pychecker import checker

def enforceBuiltin(result):
    failure = False
    if isinstance(result, (list, tuple)):
        for item in result:
            failure = failure or enforceBuiltin(item)
    elif isinstance(result, dict):
        for item in result.values():
            failure = failure or enforceBuiltin(item)
    failure =  failure or (result.__class__.__name__ \
                           not in __builtin__.__dict__)
    return failure

def filteredCall(self, *args, **kwargs):
    from mint.client import VERSION_STRING
    args = [VERSION_STRING] + list(args)
    isException, result = self._server.callWrapper(self._name,
                                                   self._authToken, args)

    if not isException:
        if enforceBuiltin(result):
            # if the return type appears to be correct, check the types
            # some items get cast to look like built-ins for str()
            # an extremely common example is sql result rows.
            raise AssertionError('XML cannot marshall return value: %s '
                                 'for method %s' % (str(result), self._name))
        return result
    else:
        self.handleError(result)

conaryDir = None
_setupPath = None
def setup():
    global _setupPath
    if _setupPath:
        return _setupPath
    global testPath
    global archivePath

    conaryPath      = os.getenv('CONARY_PATH',      os.path.realpath('../../conary-2.0'))
    conaryTestPath  = os.getenv('CONARY_TEST_PATH', os.path.realpath(os.path.join(conaryPath, '..', 'conary-test-2.0')))
    mcpPath         = os.getenv('MCP_PATH',         os.path.realpath('../../mcp'))
    mcpTestPath     = os.getenv('MCP_TEST_PATH',    os.path.realpath(os.path.join(mcpPath, 'test')))
    jobslavePath    = os.getenv('JOB_SLAVE_PATH',   os.path.realpath('../../jobslave'))
    mintPath        = os.getenv('MINT_PATH',        os.path.realpath('..'))
    mintTestPath    = os.getenv('MINT_TEST_PATH',   os.path.realpath('.'))
    raaPath         = os.getenv('RAA_PATH',         os.path.realpath('../../raa'))
    raaTestPath     = os.getenv('RAA_TEST_PATH',    os.path.realpath('../../raa-test'))
    raaPluginsPath  = os.getenv('RAA_PLUGINS_PATH', os.path.realpath('../raaplugins'))

    coveragePath    = os.getenv('COVERAGE_PATH',    os.path.realpath('../../utils'))

    sys.path = [os.path.realpath(x) for x in (mintPath, mintTestPath,
        mcpPath, mcpTestPath, jobslavePath, conaryPath, conaryTestPath,
        raaPath, raaTestPath, raaPluginsPath, coveragePath)] + sys.path
    os.environ.update(dict(CONARY_PATH=conaryPath,
        CONARY_TEST_PATH=conaryTestPath,
        MCP_PATH=mcpPath, MCP_TEST_PATH=mcpTestPath,
        MINT_PATH=mintPath, MINT_TEST_PATH=mintTestPath,
        JOB_SLAVE_PATH=jobslavePath, RAA_PATH=raaPath,
        RAA_TEST_PATH=raaTestPath, RAA_PLUGINS_PATH=raaPluginsPath,
        COVERAGE_PATH=coveragePath, 
        PYTHONPATH=(':'.join(sys.path))))

    import testhelp
    from conary_test import resources

    resources.testPath = testPath = testhelp.getTestPath()
    resources.archivePath = archivePath = testPath + '/' + "archive"

    global conaryDir

    resources.conaryDir = conaryDir = os.environ['CONARY_PATH']

    from conary.lib import util
    sys.excepthook = util.genExcepthook(True)

    # if we're running with COVERAGE_DIR, we'll start covering now
    from conary.lib import coveragehook

    # import tools normally expected in findTrove.
    from testhelp import context, TestCase, findPorts, SkipTestException
    sys.modules[__name__].context = context
    sys.modules[__name__].TestCase = TestCase
    sys.modules[__name__].findPorts = findPorts
    sys.modules[__name__].SkipTestException = SkipTestException
    sys.modules['testsuite'] = sys.modules[__name__]

    # ensure shim client errors on types that can't be sent over xml-rpc
    from mint import shimclient
    shimclient._ShimMethod.__call__ = filteredCall


    _setupPath = testPath
    return testPath

_individual = False

def isIndividual():
    global _individual
    return _individual


EXCLUDED_PATHS = ['test', 'scripts']

def main(argv=None, individual=True):
    import testhelp
    testhelp.isIndividual = isIndividual
    class rBuilderTestSuiteHandler(testhelp.TestSuiteHandler):
        suiteClass = testhelp.ConaryTestSuite

        def getCoverageDirs(self, environ):
            return environ['mint']

        def getCoverageExclusions(self, environ):
            return EXCLUDED_PATHS

    global _handler
    global _individual
    _individual = individual
    if argv is None:
        argv = list(sys.argv)
    topdir = testhelp.getTestPath()
    cwd = os.getcwd()
    if topdir not in sys.path:
        sys.path.insert(0, topdir)
    if cwd != topdir and cwd not in sys.path:
        sys.path.insert(0, cwd)

    handler = rBuilderTestSuiteHandler(individual=individual, topdir=topdir,
                                       testPath=testPath, conaryDir=conaryDir)
    _handler = handler
    results = handler.main(argv)
    sys.exit(not results.wasSuccessful())

# Marker decorators
def tests(*issues):
    '''
    Marks a function as testing one or more issues.
    If the referenced issue is a feature, the test verifies that the
    implementation is valid.
    If the issue is a bug, the test confirms that the fix is complete. The
    test should fail against the previous code, and pass with the new code.
    Note that this decorator doesn't actually do anything useful yet, it's
    just a marker.

    Example:
    @testsuite.tests('FOO-123', 'BAR-456')
    def testPonies(self):
        ...
    '''
    def decorate(func):
        func.meta_tests = issues
        return func
    return decorate

if __name__ == '__main__':
    setup()
    main(sys.argv, individual=False)

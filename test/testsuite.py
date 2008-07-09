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

    conaryPath      = os.getenv('CONARY_PATH',      os.path.realpath('../../conary'))
    conaryTestPath  = os.getenv('CONARY_TEST_PATH', os.path.realpath(os.path.join(conaryPath, '..', 'conary-test')))
    mcpPath         = os.getenv('MCP_PATH',         os.path.realpath('../../mcp'))
    mcpTestPath     = os.getenv('MCP_TEST_PATH',    os.path.realpath(os.path.join(mcpPath, 'test')))
    jobslavePath    = os.getenv('JOB_SLAVE_PATH',   os.path.realpath('../../jobslave'))
    mintPath        = os.getenv('MINT_PATH',        os.path.realpath('..'))
    mintTestPath    = os.getenv('MINT_TEST_PATH',   os.path.realpath('.'))
    raaPath         = os.getenv('RAA_PATH',         os.path.realpath('../../raa-2.1'))
    raaTestPath     = os.getenv('RAA_TEST_PATH',    os.path.realpath('../../raa-test-2.1'))
    raaPluginsPath  = os.getenv('RAA_PLUGINS_PATH', os.path.realpath('../raaplugins'))
    proddefPath     = os.getenv('PRODUCT_DEFINITION_PATH',     os.path.realpath('../../product-definition'))
    coveragePath    = os.getenv('COVERAGE_PATH',    os.path.realpath('../../utils'))
    catalogServicePath = os.getenv('CATALOG_SERVICE_PATH', os.path.realpath('../../utils'))

    #Package creator
    packageCreatorPath = os.getenv('PACKAGE_CREATOR_SERVICE_PATH',    os.path.realpath('../../package-creator-service'))
    if not os.path.exists(packageCreatorPath):
        print >> sys.stderr, "Please set PACKAGE_CREATOR_SERVICE_PATH"
        sys.exit(1)
    conaryFactoryTestPath = os.getenv('CONARY_FACTORY_TEST_PATH',    os.path.realpath('../../conary-factory-test'))
    if not os.path.exists(conaryFactoryTestPath):
        print >> sys.stderr, "Please set CONARY_FACTORY_TEST_PATH"
        sys.exit(1)

    sys.path = [os.path.realpath(x) for x in (mintPath, mintTestPath,
        mcpPath, mcpTestPath, jobslavePath, conaryPath, conaryTestPath,
        raaPath, raaTestPath, raaPluginsPath, proddefPath, coveragePath,
        packageCreatorPath, conaryFactoryTestPath, catalogServicePath )] \
                + sys.path
    os.environ.update(dict(CONARY_PATH=conaryPath,
        CONARY_TEST_PATH=conaryTestPath,
        MCP_PATH=mcpPath, MCP_TEST_PATH=mcpTestPath,
        MINT_PATH=mintPath, MINT_TEST_PATH=mintTestPath,
        JOB_SLAVE_PATH=jobslavePath, RAA_PATH=raaPath,
        RAA_TEST_PATH=raaTestPath, RAA_PLUGINS_PATH=raaPluginsPath,
        PRODUCT_DEFINITION_PATH=proddefPath,
        COVERAGE_PATH=coveragePath, 
        PACKAGE_CREATOR_SERVICE_PATH=packageCreatorPath,
        CONARY_FACTORY_TEST_PATH=conaryFactoryTestPath,
        PYTHONPATH=(':'.join(sys.path))))

    import testhelp
    from conary_test import resources

    resources.testPath = testPath = testhelp.getTestPath()
    resources.mintArchivePath = archivePath = testPath + '/' + "archive"

    # Set conary's archivePath as well
    resources.archivePath = conaryTestPath + '/archive'

    global conaryDir

    resources.conaryDir = conaryDir = os.environ['CONARY_PATH']

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

        def __init__(self, *args, **kwargs):
            self.mintDir = kwargs.pop('mintDir')
            self.pluginDir = kwargs.pop('pluginDir')
            testhelp.TestSuiteHandler.__init__(self, *args, **kwargs)

        def getCoverageDirs(self, environ):
            return [self.mintDir, self.pluginDir]

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

    mintDir = os.path.join(os.getenv('MINT_PATH'), 'mint')
    pluginDir = os.path.join(os.getenv('RAA_PLUGINS_PATH'), 'rPath')

    handler = rBuilderTestSuiteHandler(individual=individual, topdir=topdir,
                                       testPath=testPath, conaryDir=conaryDir,
                                       mintDir=mintDir, pluginDir=pluginDir)
    _handler = handler
    results = handler.main(argv)

    # Return 2 if tests failed. Python will return 1 if there was a fatal
    # error outside of the actual testing (e.g. an import error).
    rc = (not results.wasSuccessful()) and 2 or 0
    sys.exit(rc)

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

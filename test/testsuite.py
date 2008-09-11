#!/usr/bin/python2.4
# -*- mode: python -*-
#
# Copyright (c) 2005-2008 rPath, Inc.
#
import bootstrap

import sys
import os
import os.path

EXCLUDED_PATHS = ['test', 'scripts']

def isIndividual():
    from testrunner import resources
    return resources.cfg.isIndividual

def setup():
    import mint_init
    # after having set up the necessary sys.path, load the modules
    # expected here.
    mint_init.initialize()
    global context, tests, SkipTestException, TestCase, enforceBuiltin
    from testrunner.decorators import context, tests
    from testrunner.testhelp import SkipTestException
    from testrunner.testhelp import TestCase
    from mint_init import enforceBuiltin
    conaryTestPath = os.environ['CONARY_TEST_PATH']
    resources.archivePath = conaryTestPath + '/archive'

def main(argv=None, individual=True):
    if argv is None:
        argv = sys.argv
    from testrunner import testhelp, testhandler
    from testrunner import resources

    mintDir = os.path.join(os.getenv('MINT_PATH'), 'mint')
    pluginDir = os.path.join(os.getenv('RAA_PLUGINS_PATH'), 'rPath')

    cfg = resources.cfg
    cfg.coverageDirs = [mintDir, pluginDir]
    cfg.coverageExclusions = EXCLUDED_PATHS
    cfg.isIndividual = individual
    cfg.cleanTestDirs = not individual

    handler = testhandler.TestSuiteHandler(cfg, resources)
    results = handler.main(argv)

    # Return 2 if tests failed. Python will return 1 if there was a fatal
    # error outside of the actual testing (e.g. an import error).
    rc = (not results.wasSuccessful()) and 2 or 0
    sys.exit(rc)

if __name__ == '__main__':
    setup()
    main(sys.argv, individual=False)

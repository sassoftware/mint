#!/usr/bin/python
# -*- mode: python -*-
#
# Copyright (c) 2005-2009 rPath, Inc.
#
from mint_test import bootstrap

import __builtin__
import sys
import os
import os.path
from testrunner import pathManager

os.environ['DJANGO_SETTINGS_MODULE'] = 'mint.django_rest.settings_local'
from django import http
from django.conf import settings
from django.test import utils

# Django will mistakengly set this to None when running under mod_python as we
# do in our testsuite.
if http.parse_qsl is None:
    from cgi import parse_qsl
    http.parse_qsl = parse_qsl

_individual = False

def isIndividual():
    global _individual
    return _individual

def enforceBuiltin(result):
    failure = False
    if isinstance(result, (list, tuple)):
        for item in result:
            failure = failure or enforceBuiltin(item)
    elif isinstance(result, dict):
        for item in result.items():
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

def setup():
    pathManager.addExecPath('CONARY_PATH')
    conaryTestPath = pathManager.addExecPath('CONARY_TEST_PATH')
    conaryArchivePath = conaryTestPath + '/archive'
    pathManager.addResourcePath('CONARY_ARCHIVE_PATH',path=conaryArchivePath)

    global context, tests, SkipTestException, TestCase, enforceBuiltin
    from testrunner.decorators import context, tests
    from testrunner.testhelp import SkipTestException
    from testrunner.testhelp import TestCase
    
    pathManager.addExecPath('RMAKE_PATH')

    pathManager.addExecPath('MCP_PATH')

    pathManager.addExecPath('RAA_PATH')
    pathManager.addExecPath('RAA_TEST_PATH')
    
    pathManager.addExecPath('REPODATA_PATH')
    pathManager.addExecPath('RESTLIB_PATH')
    pathManager.addExecPath('CREST_PATH')
    pathManager.addExecPath('XOBJ_PATH')
    pathManager.addExecPath('XMLLIB_PATH')
    pathManager.addExecPath('PRODUCT_DEFINITION_PATH')
    pathManager.addExecPath('JOB_PATH')
    pathManager.addExecPath('STORAGE_PATH')
    pathManager.addExecPath('CATALOG_SERVICE_PATH')
    pathManager.addExecPath('CAPSULE_INDEXER_PATH')
    pathManager.addExecPath('CAPSULE_INDEXER_TEST_PATH')
    pathManager.addExecPath('SMARTFORM_PATH')
    pathManager.addExecPath('MODELS_PATH')

    pathManager.addExecPath('PACKAGE_CREATOR_SERVICE_PATH')
    path = pathManager.addExecPath('PACKAGE_CREATOR_SERVICE_TEST_PATH')
    pathManager.addResourcePath('PACKAGE_CREATOR_SERVICE_ARCHIVE_PATH',
            path + '/factory_test/archive')
    pathManager.addResourcePath('PACKAGE_CREATOR_SERVICE_FACTORY_PATH',
            path + '/recipes')

    pathManager.addExecPath('MINT_PATH')
    mintTestPath = pathManager.addExecPath('MINT_TEST_PATH')
    pathManager.addResourcePath('TEST_PATH',path=mintTestPath)
    pathManager.addResourcePath('MINT_ARCHIVE_PATH',
            path=os.path.join(mintTestPath, 'mint_test/mint_archive'))

    mintPlugins = pathManager.addExecPath('MINT_RAA_PLUGINS_PATH')
    defaultPlugins = pathManager.getPath('RAA_PATH')
    pathManager.addExecPath('RAA_PLUGINS_PATH', [defaultPlugins, mintPlugins])

   # if we're running with COVERAGE_DIR, we'll start covering now
    from conary.lib import coveragehook

    # ensure shim client errors on types that can't be sent over xml-rpc
    from mint import shimclient
    shimclient._ShimMethod.__call__ = filteredCall

    from mint_test import _apache
    sys.modules['_apache'] = _apache


def getCoverageDirs(handler, environ):
    mintDir = pathManager.getPath('MINT_PATH')
    return [ os.path.join(mintDir, 'mint'),
             os.path.join(mintDir, 'raaPlugins/rPath') 
             ]

def getExcludePaths(handler, environ):
    return ['test', 'scripts']

def sortTests(tests):
    order = {'smoketest': 0, 
             'unit_test' :1,
             'functionaltest':2}
    maxNum = len(order)
    tests = [ (test, test.index('test')) for test in tests]
    tests = sorted((order.get(test[:index+4], maxNum), test)
                   for (test, index) in tests)
    tests = [ x[1] for x in tests ]
    return tests

def setup_django_database(**kwargs):
    """
    Code taken from django.test.simple for setting up the django database for
    django tests.
    """
    try:
        if settings.DATABASE_ENGINE == 'sqlite3':
            os.unlink(settings.TEST_DATABASE_NAME)
    except OSError:
        pass
    from django.db import connections
    old_names = []
    mirrors = []
    for alias in connections:
        connection = connections[alias]
        # If the database is a test mirror, redirect it's connection
        # instead of creating a test database.
        if connection.settings_dict['TEST_MIRROR']:
            mirrors.append((alias, connection))
            mirror_alias = connection.settings_dict['TEST_MIRROR']
            connections._connections[alias] = connections[mirror_alias]
        else:
            old_names.append((connection, connection.settings_dict['NAME']))
            connection.creation.create_test_db(1, autoclobber=False)
    return old_names, mirrors

def main(argv=None, individual=True):
    global _individual
    _individual=individual

    if argv is None:
        argv = sys.argv
    from testrunner import testhelp
    setup_django_database()
    utils.setup_test_environment()
    handlerClass = testhelp.getHandlerClass(testhelp.ConaryTestSuite,
                                            getCoverageDirs,
                                            getExcludePaths,
                                            sortTests)

    handler = handlerClass(individual=_individual)
    results = handler.main(argv)

    # Need to delete the database used by django tests.
    if settings.DATABASE_ENGINE == 'sqlite3':
        try:
            os.unlink(settings.TEST_DATABASE_NAME)
        except OSError:
            pass

    sys.exit(results.getExitCode())

if __name__ == '__main__':
    setup()
    main(sys.argv, individual=False)

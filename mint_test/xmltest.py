#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#


import fixtures

import mint.server
from mint.mint_error import ParameterError
from mint.server import deriveBaseFunc, checkParam, \
    typeCheck, SERVER_VERSIONS
from testrunner.decorators import context

SKIP_TYPE_CHECK = ('callWrapper', 'loadSession', 'saveSession', 'deleteSession', 'cleanupSessions')

SKIP_PRIVATE = ('callWrapper', 'getBuildStatus', 'getGroupTroves',
                'addGroupTroveItem', 'delGroupTroveItem',
                'addGroupTroveItemByProject', 'setGroupTroveItemVersionLock',
                'getTroveVersionsByArch', 'setUserLevel', 'getGroupTrove',
                'getBuild', 'getUserPublic', 'listActiveJobs', 'delMember',
                'setBuildPublished', 'deleteBuild', 'startImageJob')

class XmlInterfaceTest(fixtures.FixturedUnitTest):
    def _getMethods(self, client, skipSet):
        keys = client.server.__class__.__dict__.keys()
        methods = []
        for funcName in keys:
            if (funcName[0] != '_') and (funcName not in skipSet):
                methods.append(deriveBaseFunc(self.mintServer.__class__.__dict__[funcName]))
        return methods

    # loop through every rpc call the server offers.
    # ensure each method has a typeCheck decorator
    @fixtures.fixture("Empty")
    def testTypeCheck(self, db, data):
        client = self.getClient("test")
        methods = self._getMethods(client, SKIP_TYPE_CHECK)
        for method in methods:
            try:
                method.__args_enforced__
            except AttributeError:
                self.fail('XML-RPC Method: %s needs a typeCheck decorator' %method.func_name)

    @fixtures.fixture("Empty")
    def testCheckParam(self, db, data):
        # test a single value for match
        param = 1
        paramType = int
        if not checkParam(param, paramType):
            self.fail("False negative for checkparam single value mode")

        # test a single value for mismatch
        param = 1
        paramType = str
        if checkParam(param, paramType):
            self.fail("False positive for checkparam single value mode")

        # test a choice of values for match
        param = 'string'
        paramType = ((int, str),)
        if not checkParam(param, paramType):
            self.fail("False negative for checkparam choice of value mode")

        # test a choice of values for mismatch
        param = False
        paramType = ((int, str),)
        if checkParam(param, paramType):
            self.fail("False positive for checkparam choice of value mode")

        #test a container for match
        param = [1, 2]
        paramType = (list, int)
        if not checkParam(param, paramType):
            self.fail("False negative for checkparam container mode")

        #test a container for mismatch
        param = (1, 2)
        paramType = (list, int)
        if checkParam(param, paramType):
            self.fail("False positive for checkparam container mode")

        #test a dict for match
        param = {'key' : 'value'}
        paramType = (dict, str)
        if not checkParam(param, paramType):
            self.fail("False negative for checkparam dict mode")

        #test a dict for mismatch
        param = {'key' : 'value'}
        paramType = (dict, int)
        if checkParam(param, paramType):
            self.fail("False positive for checkparam dict mode")

        #test a choice of containers of single values for match
        param = (1, 2)
        paramType = (((tuple, int), (tuple, str)),)
        if not checkParam(param, paramType):
            self.fail("False negative for checkparam choice of container mode")

        #test a choice of containers of single values for mismatch
        param = (1, 2)
        paramType = (((list, int), (tuple, str)),)
        if checkParam(param, paramType):
            self.fail("False positive for checkparam choice of container mode")

    @fixtures.fixture("Empty")
    def testTypeCheckBypass(self, db, data):
        class dummy:
            pass

        obj = dummy()
        obj.cfg = dummy()
        for obj.cfg.debugMode in (False, True):
            @typeCheck(int)
            def foo(obj, int):
                pass

            self.assertRaises(ParameterError, foo, self,
                              'This is not an int')

    @context("quick")
    @fixtures.fixture("Empty")
    def testPrivate(self, db, data):
        client = self.getClient("test")
        methods = self._getMethods(client, SKIP_PRIVATE)
        for method in methods:
            try:
                method.__private_enforced__
            except AttributeError:
                self.fail('XML-RPC Method: %s needs a private decorator' %method.func_name)

    @fixtures.fixture("Empty")
    def testBadCall(self, db, data):
        client = self.getClient("test")

        funcName = "someRandomFunction"
        self.failUnlessEqual(
                client.server.callWrapper(funcName,
                    ('username, userpass'), None),
                (True, ("MethodNotSupported", (funcName,))))

        funcName = '_' + funcName
        self.failUnlessEqual(
                client.server.callWrapper(funcName,
                    ('username, userpass'), None),
                (True, ("MethodNotSupported", (funcName,))))

    @fixtures.fixture("Empty")
    def testCheckVersion(self, db, data):
        client = self.getClient("test")
        server = client.server

        r = server._server.callWrapper('checkVersion', ('anonymous', 'anonymous'), ('RBUILDER_CLIENT:%d' % SERVER_VERSIONS[-1],))
        self.failUnlessEqual(r[1], SERVER_VERSIONS)

        # fake an old unversioned client
        mint.server.SERVER_VERSIONS = [1]
        try:
            r = server._server.callWrapper('checkVersion', ('anonymous', 'anonymous'), ())
            self.failUnlessEqual(r[1], [1])
        finally:
            mint.server.SERVER_VERSIONS = SERVER_VERSIONS

        # fake an old client
        self.failUnlessEqual(server._server.callWrapper('checkVersion',
                ('anonymous', 'anonymous'), ('RBUILDER_CLIENT:0',)),
            (True, ('InvalidClientVersion', 'Invalid client version 0. '
                'Server accepts client versions %d' % SERVER_VERSIONS[-1])))


#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.mint_server import deriveBaseFunc, checkParam, typeCheck, ParameterError

SKIP_TYPE_CHECK = ('callWrapper', 'loadSession', 'saveSession', 'deleteSession', 'cleanupSessions')
SKIP_PRIVATE = ('callWrapper', 'getReleaseStatus', 'getGroupTroves', 'getJobStatus', 'addGroupTroveItem', 'delGroupTroveItem', 'addGroupTroveItemByProject')

class XmlInterfaceTest(MintRepositoryHelper):
    def _getMethods(self, skipSet):
        keys = self.mintServer.__class__.__dict__.keys()
        methods = []
        for funcName in keys:
            if (funcName[0] != '_') and (funcName not in skipSet):
                methods.append(deriveBaseFunc(self.mintServer.__class__.__dict__[funcName]))
        return methods

    # loop through every rpc call the server offers.
    # ensure each method has a typeCheck decorator
    def testTypeCheck(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        methods = self._getMethods(SKIP_TYPE_CHECK)
        for method in methods:
            try:
                method.__args_enforced__
            except AttributeError:
                self.fail('XML-RPC Method: %s needs a typeCheck decorator' %method.func_name)

    def testCheckParam(self):
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

    # this test will need to go away when we turn on typeChecking in both
    # production and debug modes
    def testTypeCheckBypass(self):
        # turn off debug mode and ensure types are not checked
        self.cfg.debugMode = False

        @typeCheck(int)
        def foo(self, int):
            pass

        foo(self, 'string')

        # turn on debug mode and ensure types are checked
        self.cfg.debugMode = True

        @typeCheck(int)
        def foo(self, int):
            pass

        try:
            foo(self, 'string')
            self.fail("Illegal parameter should have failed.")
        except ParameterError:
            pass

    def testPrivate(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        methods = self._getMethods(SKIP_PRIVATE)
        for method in methods:
            try:
                method.__private_enforced__
            except AttributeError:
                self.fail('XML-RPC Method: %s needs a private decorator' %method.func_name)

    def testBadCall(self):
        funcName = "someRandomFunction"
        if self.mintServer.callWrapper(funcName, ('username, userpass'), None) != (True, ("MethodNotSupported", funcName, "")):
            self.fail("xml rpc server responded to bad method call")
        funcName = '_' + funcName
        if self.mintServer.callWrapper(funcName, ('username, userpass'), None) != (True, ("MethodNotSupported", funcName, "")):
            self.fail("xml rpc server responded to hidden method call")

if __name__ == "__main__":
    testsuite.main()

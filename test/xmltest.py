#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels
from mint.mint_server import deriveBaseFunc

SKIP_TYPE_CHECK = ('callWrapper')
SKIP_PRIVATE = ('callWrapper', 'getReleaseStatus', 'getGroupTroves')

class XmlIntrfaceTest(MintRepositoryHelper):
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

    def testPrivate(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        methods = self._getMethods(SKIP_PRIVATE)
        for method in methods:
            try:
                method.__private_enforced__
            except AttributeError:
                self.fail('XML-RPC Method: %s needs a private decorator' %method.func_name)

if __name__ == "__main__":
    testsuite.main()

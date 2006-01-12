#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import mint
from mint_server import MintServer

class ShimMintClient(mint.MintClient):
    _allowPrivate = True # enable all private methods of MintClient
    def __init__(self, cfg, authToken):
        self.server = ShimServerProxy(cfg, authToken)
        self._cfg = cfg

    def getCfg(self):
        return self._cfg

class _ShimMethod(mint._Method):
    def __init__(self, server, authToken, name):
        self._server = server
        self._authToken = authToken
        self._name = name

    def __repr__(self):
        return "<mint._ShimMethod(%r)>" % (self._name)

    def __call__(self, *args):
        isException, result = self._server.callWrapper(self._name, self._authToken, args)

        if not isException:
            return result
        else:
            self.handleError(result)

class ShimServerProxy(mint.ServerProxy):
    def __init__(self, cfg, authToken):
        self._cfg = cfg
        self._authToken = authToken
        self._server = MintServer(self._cfg, allowPrivate = True)

    def __getattr__(self, name):
        return _ShimMethod(self._server, self._authToken, name)

    def __repr__(self):
        return "ShimServerProxy(%s, %s)" % (self._cfg, self._authToken)

    def __str__(self):
        return self.__repr__()

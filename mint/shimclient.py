#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import mint
from mint_server import MintServer

class ShimMintClient(mint.MintClient):
    def __init__(self, cfg, authToken):
        self.server = ShimServerProxy(cfg, authToken)

class _ShimMethod(mint._Method):
    def __init__(self, cfg, authToken, name):
        self.__cfg = cfg
        self.__authToken = authToken
        self.__name = name

    def __repr__(self):
        return "<mint._ShimMethod(%r)>" % (self._ShimMethod__name)

    def __call__(self, *args):
        server = MintServer(self.__cfg)
        isException, result = server.callWrapper(self.__name, self.__authToken, args)

        if not isException:
            return result
        else:
            self.handleError(result)

class ShimServerProxy(mint.ServerProxy):
    def __init__(self, cfg, authToken):
        self.__cfg = cfg
        self.__authToken = authToken

    def __getattr__(self, name):
        return _ShimMethod(self.__cfg, self.__authToken, name)

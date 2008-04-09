#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
import weakref

from mint import client
from mint.client import VERSION_STRING
from mint.server import MintServer

class ShimMintClient(client.MintClient):
    _allowPrivate = True # enable all private methods of MintClient
    def __init__(self, cfg, authToken):
        self.server = ShimServerProxy(cfg, authToken)
        self._cfg = cfg

    def getCfg(self):
        return self._cfg

class _ShimMethod(client._Method, object):
    weakRefs = ('_server',)
    def __init__(self, server, authToken, name):
        self._server = server
        self._authToken = authToken
        self._name = name

    def __repr__(self):
        return "<client._ShimMethod(%r)>" % (self._name)

    def __call__(self, *args):
        args = [VERSION_STRING] + list(args)
        isException, result = self._server.callWrapper(self._name,
                                                       self._authToken, tuple(args))

        if not isException:
            return result
        else:
            self.handleError(result)

    def __getattribute__(self, name):
        if name in _ShimMethod.weakRefs:
            return object.__getattribute__(self, name)()
        return object.__getattribute__(self, name)

    def __setattr__(self, name, val):
        if name in _ShimMethod.weakRefs and not isinstance(val, weakref.ref):
            return object.__setattr__(self, name, weakref.ref(val))
        return object.__setattr__(self, name, val)

class ShimServerProxy(client.ServerProxy):
    def __init__(self, cfg, authToken):
        self._cfg = cfg
        self._authToken = authToken
        self._server = MintServer(self._cfg, allowPrivate = True)

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return _ShimMethod(self._server, self._authToken, name)

    def __repr__(self):
        return "ShimServerProxy(%s, %s)" % (self._cfg, self._authToken)

    def __str__(self):
        return self.__repr__()

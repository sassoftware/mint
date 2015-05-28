#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import weakref

from mint import client
from mint.client import VERSION_STRING
from mint.server import MintServer

class ShimMintClient(client.MintClient):
    _allowPrivate = True # enable all private methods of MintClient
    def __init__(self, cfg, authToken, db=None):
        self.server = ShimServerProxy(cfg, authToken, db)
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
        if name.startswith('__'):
            raise AttributeError(name)
        if name in _ShimMethod.weakRefs:
            return object.__getattribute__(self, name)()
        return object.__getattribute__(self, name)

    def __setattr__(self, name, val):
        if name in _ShimMethod.weakRefs and not isinstance(val, weakref.ref):
            return object.__setattr__(self, name, weakref.ref(val))
        return object.__setattr__(self, name, val)

class ShimServerProxy(client.ServerProxy):
    def __init__(self, cfg, authToken, db=None):
        self._cfg = cfg
        self._authToken = authToken
        self._server = MintServer(self._cfg, allowPrivate = True, db=db)

    def __hasattr__(self, name):
        if name.startswith('__'):
            return False

    def __getattr__(self, name):
        if name.startswith('__'):
            raise AttributeError(name)
        return _ShimMethod(self._server, self._authToken, name)

    def __repr__(self):
        return "ShimServerProxy(%s, %s)" % (self._cfg, self._authToken)

    def __str__(self):
        return self.__repr__()

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


import socket
from collections import namedtuple
from conary.lib import networking
from conary.lib import util
from conary.lib.http import connection
from conary.lib.http import request
from conary.repository import transport


class CredentialsClient(object):
    def __init__(self):
        tr = UNIXTransport()
        url = unixURL('/tmp/mintcred.sock', '/RPC2')
        self.proxy = util.ServerProxy(url, tr)

    def wrap(self, value, restrictions=None):
        store = 'default'
        options = {}
        if restrictions:
            options['restrictions'] = restrictions
        return self.proxy.wrap(store, value, options)[0]

    def unwrap(self, value):
        store = 'default'
        return self.proxy.unwrap(store, value)[0]


class UNIXPath(namedtuple('UNIXPath', 'path'), networking.BaseAddress):
    __slots__ = ()

    def __new__(cls, path):
        return tuple.__new__(cls, (path,))

    def __str__(self):
        return self.path

    def isPrecise(self):
        return True


class UNIXConnection(connection.Connection):
    def connectSocket(self):
        host = self.local.hostport.host
        if not isinstance(host, UNIXPath):
            return super(UNIXConnection, self).connectSocket()
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(host.path)
        return sock


class UNIXOpener(transport.XMLOpener):
    connectionFactory = UNIXConnection

class UNIXTransport(transport.Transport):
    openerFactory = UNIXOpener


def unixURL(path, reqpath):
    return request.URL('http', (None, None),
            networking.HostPort(UNIXPath(path), 80), reqpath)

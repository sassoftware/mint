#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import sys
import xmlrpclib

import config

class Client:
    def __init__(self, server):
        self.server = ServerProxy(server)

class MintClient(Client):
    def newProject(self, name, hostname, desc):
        return self.server.newProject(name, hostname, desc)

class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return _Method(self.__request, name)

class _Method(xmlrpclib._Method):
    def __repr__(self):
        return "<mint._Method(%s, %r)>" % (self._Method__send, self._Method__name)

    def __str__(self):
        return self.__repr__()

    def __call__(self, *args):
        isException, result = self.__send(self.__name, args)
        if not isException:
            return result
        else:
            self.handleError(result)

    def handleError(self, result):
        exceptionName = result[0]
        exceptionArgs = result[1:]

        raise UnknownException(exceptionName, exceptionArgs)


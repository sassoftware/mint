#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import sys
import xmlrpclib

import conary

from mint_error import MintError
import users
import config

class Client:
    def __init__(self, server):
        self.server = ServerProxy(server)

class MintClient(Client):
    def newProject(self, name, hostname, desc):
        return self.server.newProject(name, hostname, desc)

    def checkAuth(self):
        authTuple = self.server.checkAuth()
        print >> sys.stderr, authTuple
        sys.stderr.flush()
        return users.Authorization(*authTuple)

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

        if exceptionName == "UserAlreadyExists":
            from repository.netrepos.netauth import UserAlreadyExists
            raise UserAlreadyExists
        elif exceptionName == "MethodNotSupported":
            raise MethodNotSupported
        else:
            raise UnknownException(exceptionName, exceptionArgs)

class UnknownException(Exception):
    def __str__(self):
        return "%s %s" % (self.eName, self.eArgs)

    def __init__(self, eName, eArgs):
        self.eName = eName
        self.eArgs = eArgs

class MethodNotSupported(MintError):
    def __str__(self):
        return "method not supported by XMLRPC server"

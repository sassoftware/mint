#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import base64
import os

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

from server import http
from web import webauth
from repository.netrepos import netserver

class CookieHttpHandler(http.HttpHandler):
    def _requestAuth(self):
        return self._redirect("/login")

    def _methodHandler(self):
        """Handle either an HTTP POST or GET command."""

        if 'authToken' in self.cookies:
            auth = base64.decodestring(self.cookies['authToken'].value)
            authToken = auth.split(":")
        else:
            authToken = ('anonymous', 'anonymous')

        self.auth = authToken

        try:
            method = self._getHandler(self.cmd)
        except AttributeError:
            return apache.HTTP_NOT_FOUND

        d = dict(self.fields)
        d['auth'] = self.auth

        try:
            return method(**d)
        except netserver.InsufficientPermission:
            # good password but no permission, don't ask for a new password
            return apache.HTTP_FORBIDDEN
        except http.InvalidPassword:
            # if password is invalid, request a new one
            return self._requestAuth()
        except:
            self._write("error", error = traceback.format_exc())
            return apache.OK

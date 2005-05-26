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
        self.writeFn = self.req.write
        cmd = os.path.basename(self.req.path_info)

        cookies = Cookie.get_cookies(self.req, Cookie.Cookie)

        if 'authToken' in cookies:
            auth = base64.decodestring(cookies['authToken'].value)
            authToken = auth.split(":")
        else:
            authToken = ('anonymous', 'anonymous')

        self.auth = authToken

        if cmd.startswith('_'):
            return apache.HTTP_NOT_FOUND

        self.req.content_type = "application/xhtml+xml"

        try:
            method = self._getHandler(cmd)
        except AttributeError:
            return apache.HTTP_NOT_FOUND

        self.fields = FieldStorage(self.req)

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

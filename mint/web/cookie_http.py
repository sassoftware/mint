#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import base64
import os
import sys
import traceback

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

from server import http
from repository import shimclient
from web import webauth
from repository.netrepos import netserver

class CookieHttpHandler(http.HttpHandler):
    def _requestAuth(self):
        return self._redirect("/login")

    def _getAuth(self):
        if 'authToken' in self.cookies:
            auth = base64.decodestring(self.cookies['authToken'].value)
            authToken = auth.split(":")
        else:
            authToken = ('anonymous', 'anonymous')
            
        return authToken

#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import conary
from server import http

class CookieHttpHandler(http.HttpHandler):
    def _requestAuth(self):
        return self._redirect("login")

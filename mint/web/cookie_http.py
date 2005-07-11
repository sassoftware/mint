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

    # XXX: I'm wondering if this is the best approach.
    # maybe it would be better to override _getHandler and
    # provide a list of explicitly-allowed methods. opt-in
    # instead of opt-out.
    #
    # remove some disallowed methods for mint:
    del http.HttpHandler.main
    del http.HttpHandler.metadata
    del http.HttpHandler.chooseBranch
    del http.HttpHandler.getMetadata
    del http.HttpHandler.updateMetadata
    del http.HttpHandler.userlist
    del http.HttpHandler.addPermForm
    del http.HttpHandler.addPerm
    del http.HttpHandler.addGroupForm
    del http.HttpHandler.manageGroupForm
    del http.HttpHandler.manageGroup
    del http.HttpHandler.addGroup
    del http.HttpHandler.deleteGroup
    del http.HttpHandler.deletePerm
    del http.HttpHandler.addUser
    del http.HttpHandler.deleteUser
    del http.HttpHandler.chPassForm
    del http.HttpHandler.chPass

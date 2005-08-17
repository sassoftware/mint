#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import base64
import os
import sys

from server import http
from repository import shimclient
from templates import repos
from app import MintApp

class CookieHttpHandler(MintApp, http.HttpHandler):
    def __init__(self, req, cfg, repServer, protocol, port):
        http.HttpHandler.__init__(self, req, cfg, repServer, protocol, port)

        if 'mint.web.templates.repos' in sys.modules:
            self.reposTemplatePath = os.path.dirname(sys.modules['mint.web.templates.repos'].__file__) + "/repos/"
            
    def _requestAuth(self):
        return self._redirect("/")

    def _getHandler(self, cmd, auth):
        self.repos = shimclient.ShimNetClient(
            self.repServer, self._protocol, self._port, auth.getToken(), self.repServer.map)
        self.serverName = self.repServer.name
        return MintApp._getHandler(self, cmd, auth)

    def _getAuth(self):
        if 'authToken' in self.cookies:
            auth = base64.decodestring(self.cookies['authToken'].value)
            authToken = auth.split(":")
        else:
            authToken = ('anonymous', 'anonymous')
            
        return authToken

    def _write(self, templateName, **values):
        MintApp._write(self, templateName, templatePath = self.reposTemplatePath, **values)

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

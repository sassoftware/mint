#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import base64
import os
import sys

from server import http
from repository import netclient 
from templates import repos
from webhandler import WebHandler
from mint.session import SqlSession

class ConaryHandler(WebHandler, http.HttpHandler):
    def __init__(self, req, cfg, repServer):
        protocol = 'http'
        port = 80
        self.repServer = repServer
        
        http.HttpHandler.__init__(self, req, cfg, self.repServer, protocol, port)

        if 'mint.web.templates.repos' in sys.modules:
            self.reposTemplatePath = os.path.dirname(sys.modules['mint.web.templates.repos'].__file__) + "/repos/"
    
    def handle(self, context):
        self.__dict__.update(**context)

        # set up the netclient
        self.serverName = self.req.hostname

        path = self.req.path_info.split("/")
        self.cmd = path[3]
        if path[1] == "repos":
            self.serverName = path[2] + "." + self.cfg.domainName
        
        self.project = self.client.getProjectByFQDN(self.serverName)
        projectName = self.project.getHostname()
        self.repositoryMap = {self.serverName: 'http://%s/repos/%s/' % (self.siteHost, projectName)}
        self.repos = netclient.NetworkRepositoryClient(self.repositoryMap)

        return self._handle

    def _handle(self, *args, **kwargs):
        return self._methodHandler()
   
    def _requestAuth(self):
        return self._redirect("/")

    def _getHandler(self, cmd):
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            return self._404
        return method

    def _getAuth(self):
        return self.authToken

    def _write(self, templateName, **values):
        WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)

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

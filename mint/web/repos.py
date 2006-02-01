#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#
import base64
import os
import sys
import traceback

from mod_python import apache

from conary.server import http
from conary.repository import errors
from conary.repository.shimclient import ShimNetClient
from conary import conaryclient

from webhandler import WebHandler, normPath, HttpForbidden, HttpNotFound
from templates import repos
from mint.session import SqlSession
from mint import database

class ConaryHandler(WebHandler, http.HttpHandler):
    def __init__(self, req, cfg, repServer = None):
        protocol = 'http'
        port = 80

        #If the browser can support it, give it what it wants.
        if 'application/xhtml+xml' in req.headers_in.get('Accept', ''):
            self.content_type = 'application/xhtml+xml'
            self.output = 'xhtml'

        if repServer:
            self.repServer = repServer
            self.troveStore = self.repServer.troveStore
        if 'mint.web.templates.repos' in sys.modules:
            self.reposTemplatePath = os.path.dirname(sys.modules['mint.web.templates.repos'].__file__) + "/repos/"

    def handle(self, context):
        self.__dict__.update(**context)

        # set up the netclient
        self.serverName = self.req.hostname

        path = self.req.path_info.split("/")
        self.cmd = path[3]
        try:
            if path[1] == "repos":
                self.project = self.client.getProjectByHostname(path[2])
                self.serverName = self.project.getLabel().split("@")[0]
            else:
                self.project = self.client.getProjectByFQDN(self.serverName)
        except database.ItemNotFound:
            raise HttpNotFound

        self.basePath += "repos/%s" % self.project.getHostname()
        self.basePath = normPath(self.basePath)

        if self.auth:
            self.userLevel = self.project.getUserLevel(self.auth.userId)

        return self._handle

    def _handle(self, *args, **kwargs):
        """Handle either an HTTP POST or GET command."""

        if self.project.external:
            useSSL = None # use the label as-is for external projects
        else:
            useSSL = self.cfg.SSL
        cfg = self.project.getConaryConfig(overrideSSL = True, overrideAuth = True,
                                           newUser = self.authToken[0],
                                           newPass = self.authToken[1],
                                           useSSL = useSSL)
        self.authToken = (self.authToken[0], self.authToken[1], None, None)

        # FIXME: hack
        # if we are looking at a trove, and the trove points to an external
        # repository, we need to instantiate a netclient vice shimclient

        # for now the troveInfo page itself must be loaded with netClient
        # because we do not have a version available.

        repos = None
        needsExternal = False
        extURIs = ('/files', '/troveInfo', '/getFile')
        if True in [self.req.uri.endswith(x) for x in extURIs]:
            versionStr = ''
            if self.req.uri.endswith('files'):
                versionStr = str(kwargs['v'])
            elif self.req.uri.endswith('getFile'):
                versionStr = str(kwargs['fileV'])

            if versionStr:
                needsExternal = self.client.versionIsExternal(versionStr)
            else:
                needsExternal = True

        ### end hack. ###

        if self.project.external or needsExternal:
            self.repos = conaryclient.ConaryClient(cfg).getRepos()
        else:
            self.repos = ShimNetClient(self.repServer, 'http', 80,
                                       self.authToken, cfg.repositoryMap,
                                       cfg.user)

        try:
            method = self.__getattribute__(self.cmd)
        except AttributeError:
            raise HttpNotFound

        d = self.fields
        d['auth'] = self.authToken
        try:
            output = method(**d)
            return output
        except (http.InvalidPassword, errors.OpenError):
            return self._requestAuth(d)

    def _requestAuth(self, d):
        # try to fall back to anonymous and rerun the handler
        if self.authToken[0] != 'anonymous':
            self.authToken = ('anonymous', 'anonymous')
            return self._handle(**d)
        else:
            raise HttpForbidden

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)

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
    del http.HttpHandler.deleteGroup
    del http.HttpHandler.deleteUser
    del http.HttpHandler.addPermForm
    del http.HttpHandler.addPerm
    del http.HttpHandler.addGroupForm
    del http.HttpHandler.manageGroupForm
    del http.HttpHandler.manageGroup
    del http.HttpHandler.addGroup
    del http.HttpHandler.deletePerm
    del http.HttpHandler.addUser
    del http.HttpHandler.chPassForm
    del http.HttpHandler.chPass

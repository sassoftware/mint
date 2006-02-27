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

        path = self.req.uri.split("/")
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
            useSSL = False
            overrideAuth = False
        else:
            useSSL = self.cfg.SSL
            overrideAuth = True

            # try as a specified user, if fails, fall back to anonymous
            if not self.repServer.auth.check((self.authToken[0], self.authToken[1], None, None)):
                self.authToken = ('anonymous', 'anonymous', None, None)

        cfg = self.project.getConaryConfig(overrideSSL = True,
                                           overrideAuth = overrideAuth,
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

        output = method(**d)
        return output

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)

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
    del http.HttpHandler.editPermForm
    del http.HttpHandler.addUserForm
    del http.HttpHandler.pgpNewKeyForm
    del http.HttpHandler.editPerm
    del http.HttpHandler.submitPGPKey

    allowedMethods = ('getOpenPGPKey', 'pgpAdminForm', 'pgpChangeOwner',
                      'files', 'troveInfo', 'browse', 'getFile')

    for method in http.HttpHandler.__dict__.keys():
        if not (method.startswith('_') or method in allowedMethods):
            if callable(http.HttpHandler.__dict__[method]):
                print >> sys.stderr, "Warning: conary handler method is not explicitly allowed: %s\n please updte repos.py" % method


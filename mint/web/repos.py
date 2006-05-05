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

from mint import database
from mint.session import SqlSession
from mint.web.templates import repos
from mint.web.webhandler import WebHandler, normPath, HttpForbidden, HttpNotFound

from conary.server import http
from conary.repository import errors
from conary.repository.shimclient import ShimNetClient
from conary import conaryclient


class ConaryHandler(WebHandler, http.HttpHandler):
    def _filterAuth(self, **kwargs):
        memberList = kwargs.get('memberList', [])
        if isinstance(memberList, str):
            memberList = [memberList]
        if self.cfg.authUser in memberList:
            return self._write("error", shortError="Invalid User Name",
                    error = "A user name you have selected is invalid.")
        if kwargs.get('userGroupName', None) == self.cfg.authUser:
            return self._write("error", shortError="Invalid Group Name",
                    error = "The group name you are attempting to edit is invalid.")
        return None

    def manageGroup(self, **kwargs):
        return self._filterAuth(**kwargs) or \
               http.HttpHandler.manageGroup(self, **kwargs)

    def deleteGroup(self, **kwargs):
        return self._filterAuth(**kwargs) or \
               http.HttpHandler.deleteGroup(self, **kwargs)

    def addGroup(self, **kwargs):
        return self._filterAuth(**kwargs) or \
               http.HttpHandler.addGroup(self, **kwargs)

    def __init__(self, req, cfg, repServer = None):
        protocol = 'http'
        port = 80

        if repServer:
            self.repServer = repServer
            self.troveStore = self.repServer.troveStore
        if 'mint.web.templates.repos' in sys.modules:
            self.reposTemplatePath = os.path.dirname(sys.modules['mint.web.templates.repos'].__file__)

    def handle(self, context):
        self.__dict__.update(**context)

        # set up the netclient
        self.serverName = self.req.hostname

        path = self.req.path_info.split("/")
        if len(path) < 4:
            raise HttpNotFound
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
            overrideAuth = False
        else:
            # try as a specified user, if fails, fall back to anonymous
            overrideAuth = True
            if not self.repServer.auth.check((self.authToken[0], self.authToken[1], None, None)):
                self.authToken = ('anonymous', 'anonymous', None, None)

        cfg = self.project.getConaryConfig(overrideAuth = overrideAuth,
                                           newUser = self.authToken[0],
                                           newPass = self.authToken[1])
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

        if self.auth.admin:
            # if we are admin, we have the right to touch any repo, but that
            # particular repo might not know our credentials (not a project
            # member)... so use the auth user.
            saveToken = self.authToken
            self.authToken = (self.cfg.authUser, self.cfg.authPass, None, None)
            try:
                d['auth'] = self.authToken
                output = method(**d)
            finally:
                # carefully restore old credentials so that this code can work
                # outside of mod-python environments.
                self.authToken = saveToken
        else:
            output = method(**d)
        return output

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)

    del http.HttpHandler.main
    del http.HttpHandler.metadata
    del http.HttpHandler.chooseBranch
    del http.HttpHandler.getMetadata
    del http.HttpHandler.updateMetadata
    del http.HttpHandler.deleteUser
    del http.HttpHandler.addUser
    del http.HttpHandler.chPassForm
    del http.HttpHandler.chPass
    del http.HttpHandler.addUserForm
    del http.HttpHandler.pgpNewKeyForm
    del http.HttpHandler.submitPGPKey

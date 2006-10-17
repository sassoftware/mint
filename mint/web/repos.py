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
from mint import userlevels
from mint.session import SqlSession
from mint.web.templates import repos
from mint.web.webhandler import WebHandler, normPath, HttpForbidden, HttpNotFound

from conary import versions
from conary.server import http
from conary.repository import errors
from conary.repository.shimclient import ShimNetClient
from conary import conaryclient
from conary import errors as conaryerrors

# When Conary implements a new method in http.HttpHandler that needs
# to be exposed in rBuilder, add the name of the method here.
allowedMethods = ('getOpenPGPKey', 'pgpAdminForm', 'pgpChangeOwner',
    'files', 'troveInfo', 'browse', 'getFile', 'userlist',
    'deleteGroup', 'addPermForm', 'addPerm', 'addGroupForm',
    'manageGroupForm', 'manageGroup', 'addGroup',
    'deletePerm', 'editPermForm', 'editPerm')

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

        path = self.req.uri[len(self.cfg.basePath):].split("/")
        if len(path) < 3:
            raise HttpNotFound
        self.cmd = path[2]
        try:
            if path[0] == "repos":
                self.project = self.client.getProjectByHostname(path[1])
                serverName = self.project.getLabel().split("@")[0]
            else:
                serverName = self.req.hostname
                self.project = self.client.getProjectByFQDN(serverName)
        except database.ItemNotFound:
            raise HttpNotFound

        self.serverNameList = [serverName]

        self.userLevel = self.project.getUserLevel(self.auth.userId)
        self.isOwner  = (self.userLevel == userlevels.OWNER) or self.auth.admin
        self.isWriter = (self.userLevel in userlevels.WRITERS) or self.auth.admin
        self.isRemoteRepository = self.project.external

        self.basePath += "repos/%s" % self.project.getHostname()
        self.basePath = normPath(self.basePath)

        return self._handle

    def _handle(self, *args, **kwargs):
        """Handle either an HTTP POST or GET command."""

        localMirror = self.client.isLocalMirror(self.project.id)
        if self.project.external and not localMirror:
            overrideAuth = False
        else:
            # try as a specified user, if fails, fall back to anonymous
            overrideAuth = True
            if not self.repServer.auth.check((self.authToken[0], self.authToken[1], None, None)):
                self.authToken = ('anonymous', 'anonymous', None, None)

        cfg = self.project.getConaryConfig(overrideAuth = overrideAuth,
                                           newUser = self.authToken[0],
                                           newPass = self.authToken[1])
        conarycfgFile = os.path.join(self.cfg.dataPath, 'config', 'conaryrc')
        if os.path.exists(conarycfgFile):
            cfg.read(conarycfgFile)

        self.authToken = (self.authToken[0], self.authToken[1], None, None)

        if 'repServer' not in self.__dict__:
            self.repos = conaryclient.ConaryClient(cfg).getRepos()
        else:
            self.repos = ShimNetClient(self.repServer, 'http', 80,
                                       self.authToken, cfg.repositoryMap,
                                       cfg.user)

        # make sure we explicitly allow this method
        if self.cmd not in allowedMethods:
            raise HttpNotFound
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
            try:
                output = method(**d)
            except http.InvalidPassword:
                raise HttpForbidden
            except conaryerrors.InvalidRegex, e:
                return self._write("error",
                                   shortError = "Invalid Regular Expression",
                                   error = str(e))
        finally:
            # carefully restore old credentials so that this code can work
            # outside of mod-python environments.
            if self.auth.admin:
                self.authToken = saveToken
        return output

    def _write(self, templateName, **values):
        return WebHandler._write(self, templateName, templatePath = self.reposTemplatePath, **values)

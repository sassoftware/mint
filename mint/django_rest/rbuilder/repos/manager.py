#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#

from StringIO import StringIO

from django.db import connection
from django.core.exceptions import ObjectDoesNotExist

from conary import changelog
from conary.conaryclient import filetypes
from conary.repository import errors as reposerrors
from mint.rest import errors as resterrors

from mint import userlevels
from mint.db import repository as reposdbmgr
from mint.lib import unixutils

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.repos import models
from mint.django_rest.rbuilder.projects import models as projectmodels

_cachedCfg = None

class ReposManager(basemanager.BaseManager, reposdbmgr.RepomanMixin):

    def __init__(self, *args, **kwargs):
        basemanager.BaseManager.__init__(self, *args, **kwargs)
        bypass = kwargs.pop('bypass', False)
        self._repoInit(bypass=bypass)

    @property
    def db(self):
        return connection

    @exposed
    def createRepositoryForProject(self, project, createMaps=True):
        repos = self.getRepositoryForProject(project)

        self.generateConaryrcFile()

        if repos.hasDatabase:
            # Create the repository infrastructure (db, dirs, etc.).
            repos.create()

            # Create users and roles
            self.populateUsers(repos)

    def populateUsers(self, repos):
        if not repos.isHidden:
            self.addUser(repos, 'anonymous', password='anonymous',
                    level=userlevels.USER)

        # here we automatically create the USER and DEVELOPER levels
        # This avoids the chance of paying a high price for adding
        # them later - instead we amortize the cost over every commit
        if not repos.isExternal:
            netServer = repos.getNetServer()
            self._getRoleForLevel(netServer, userlevels.USER)
            self._getRoleForLevel(netServer, userlevels.DEVELOPER)
            self._getRoleForLevel(netServer, userlevels.OWNER)

        # add the auth user so we can add additional permissions
        # to this repository
        self.addUser(repos, self.cfg.authUser,
                password=self.cfg.authPass, level=userlevels.ADMIN)

    def _getRoleForLevel(self, reposServer, level):
        """
        Gets the role name for the given level, creating the role on
        the fly if necessary
        """
        roleName, canWrite, canAdmin = reposdbmgr.ROLE_PERMS[level]

        try:
            reposServer.auth.addRole(roleName)
        except reposerrors.RoleAlreadyExists:
            # assume that everything is good.
            return roleName
        else:
            reposServer.auth.addAcl(roleName, trovePattern=None, label=None,
                    write=canWrite, remove=canAdmin)
            reposServer.auth.setMirror(roleName, canAdmin)
            reposServer.auth.setAdmin(roleName, canAdmin)
        return roleName

    def addUserByMd5(self, repos, username, salt, password, level):
        reposServer = repos.getShimServer()
        role = self._getRoleForLevel(reposServer, level)
        try:
            reposServer.auth.addUserByMD5(username, salt.decode('hex'), password)
        except reposerrors.UserAlreadyExists:
            reposServer.auth.deleteUserByName(username, deleteRole=False)
            reposServer.auth.addUserByMD5(username, salt.decode('hex'), password)
        reposServer.auth.setUserRoles(username, [role])

    def addUser(self, repos, username, password, level):
        reposServer = repos.getShimServer()
        role = self._getRoleForLevel(reposServer, level)
        try:
            reposServer.auth.addUser(username, password)
        except reposerrors.UserAlreadyExists:
            reposServer.auth.deleteUserByName(username, deleteRole=False)
            reposServer.auth.addUser(username, password)
        reposServer.auth.setUserRoles(username, [role])

    def editUser(self, repos, username, level):
        reposServer = repos.getShimServer()
        role = self._getRoleForLevel(reposServer, level)
        reposServer.auth.setUserRoles(username, [role])

    def deleteUser(self, repos, username):
        reposServer = repos.getShimServer()
        reposServer.auth.deleteUserByName(username, deleteRole=False)

    def changePassword(self, repos, username, password):
        reposServer = repos.getShimServer()
        reposServer.auth.changePassword(username, password)

    def addLabel(self, project, fqdn, url, authInfo):
        authUser = authPass = entitlement = ''
        authType = authInfo.auth_type
        if authType == 'entitlement':
            entitlement = authInfo.entitlement
        elif authType == 'userpass':
            authUser, authPass = authInfo.user_name, authInfo.password

        # This table needs to go away, with the authentication bits moved
        # into projects and the rest dropped. Until then, we need a dummy
        # label as too many things depend on it being a label even though
        # they really just need a FQDN.
        label = fqdn + "@rpl:2"

        newLabel = models.Label(project=project, label=label, url=url,
            auth_type=authType, user_name=authUser, password=authPass,
            entitlement=entitlement)
        newLabel.save()

    @exposed
    def generateConaryrcFile(self):
        global _cachedCfg
        _cachedCfg = None
        if not self.cfg.createConaryRcFile:
            return
        repoMaps = self._getFullRepositoryMap()

        fObj_v0 = unixutils.atomicOpen(self.cfg.conaryRcFile, 
                                       chmod=0644)
        fObj_v1 = unixutils.atomicOpen(self.cfg.conaryRcFile + "-v1", 
                                       chmod=0644)
        for host, url in repoMaps.iteritems():
            fObj_v0.write('repositoryMap %s %s\n' % (host, url))
            fObj_v1.write('repositoryMap %s %s\n' % (host, url))
        # add proxy stuff for version 1 config clients
        if self.cfg.useInternalConaryProxy:
            fObj_v1.write('conaryProxy http http://%s.%s\n' % (
                self.cfg.hostName, self.cfg.siteDomainName))
            fObj_v1.write('conaryProxy https https://%s\n' % (
                self.cfg.secureHost,))
        self.cfg.displayKey('proxy', out=fObj_v1)

        fObj_v0.commit()
        fObj_v1.commit()

    def _getFullRepositoryMap(self):
        repoMap = {}
        for handle in self.iterRepositories(hidden=False, disabled=False):
            repoMap[handle.fqdn] = handle.getURL()
        return repoMap

    @exposed
    def getRepositoryForProject(self, project):
        projectInfo = {}
        projectInfo["projectId"] = project.pk
        projectInfo["shortname"] = str(project.short_name)
        projectInfo["fqdn"] = str(project.repository_hostname)
        projectInfo["external"] = project.external
        projectInfo["hidden"] = project.hidden
        projectInfo["commitEmail"] = project.commit_email and str(project.commit_email)
        projectInfo["database"] = project.database and str(project.database)

        try:
            label = models.Label.objects.get(project=project)
            projectInfo["localMirror"] = bool(len(
                project.inbound_mirrors.all()))
            projectInfo["url"] = label.url and str(label.url)
            projectInfo["authType"] = str(label.auth_type)
            projectInfo["username"] = label.user_name and str(label.user_name)
            projectInfo["entitlement"] = label.entitlement and str(label.entitlement)
            projectInfo["password"] = label.password and str(label.password)
        except models.Label.DoesNotExist:
            projectInfo["localMirror"] = None
            projectInfo["url"] = None
            projectInfo["authType"] = None
            projectInfo["username"] = None
            projectInfo["entitlement"] = None
            projectInfo["password"] = None

        return reposdbmgr.RepositoryHandle(self, projectInfo)
        

    def getRepositoryFromFQDN(self, fqdn):
        try:
            project = projectmodels.Project.objects.get(repository_hostname=fqdn)
        except ObjectDoesNotExist:
            raise resterrors.ProductNotFound
        return self.getRepositoryForProject(project)

    def iterRepositories(self, **conditions):
        for project in projectmodels.Project.objects.filter(**conditions):
            yield self.getRepositoryForProject(project)

    @exposed
    def createSourceTrove(self, fqdn, trovename, buildLabel, 
                          upstreamVersion, streamMap, changeLogMessage,
                          factoryName=None, admin=False, metadata=None):
        # Get repository + client
        if admin:
            client = self.getAdminClient(write=True)
        else:
            client = self.getUserClient()

        # Sanitize input
        if ':' not in trovename:
            trovename += ':source'

        if not changeLogMessage.endswith('\n'):
            changeLogMessage += '\n'

        # create a pathdict out of the streamMap
        pathDict = {}
        for filename, filestream in streamMap.iteritems():
            if isinstance(filestream, str):
                filestream = StringIO(filestream)
            if hasattr(filestream, 'getContents'):
                fileobj = filestream
            else:
                fileobj = filetypes.RegularFile(contents=filestream,
                                           config=True)

            pathDict[filename] = fileobj

        # create the changelog message using the currently
        # logged-on user's username and fullname, if available
        newchangelog = changelog.ChangeLog(self.auth.username or '(unset)',
                self.auth.fullName or '(unset)', changeLogMessage.encode('utf8'))

        # create a change set object from our source data
        changeSet = client.createSourceTrove(str(trovename), str(buildLabel),
                str(upstreamVersion), pathDict, newchangelog,
                factory=factoryName, metadata=metadata)

        # commit the change set to the repository
        client.getRepos().commitChangeSet(changeSet)

    @exposed
    def getAdminClient(self, write=False):
        """
        Get a conary client object with access to all repositories. If C{write}
        is set then the client can write to the repositories, otherwise it will
        have only read access.

        All external projects will have full read access, as if using the
        built-in conary proxy.
        """
        if write:
            userId = reposdbmgr.ANY_WRITER
        else:
            userId = reposdbmgr.ANY_READER
        return self.getClient(userId)

    @exposed
    def getUserClient(self):
        """
        Get a conary client with the permissions of the current user. This
        includes hiding private projects the user does not have access to, etc.

        All external projects will have full read access, as if using the
        built-in conary proxy. Additionally, site admins will have admin access
        to any repository.
        """
        if self.auth.admin:
            userId = reposdbmgr.ANY_WRITER
        elif self.auth.userId < 0:
            userId = reposdbmgr.ANONYMOUS
        else:
            userId = self.auth.userId
        client = self.getClient(userId)
        if self.auth.username:
            client.cfg.name = self.auth.username
            client.cfg.contact = self.auth.fullName or ''
        return client

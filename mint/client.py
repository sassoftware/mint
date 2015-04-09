#
# Copyright (c) SAS Institute Inc.
#

import time
import xmlrpclib

from mint import builds
from mint import mint_error
from mint.rest import errors as rest_error
from mint import projects
from mint import users
from mint.mint_error import *

# server.py has a history of XMLRPC API changes
CLIENT_VERSIONS = [6, 7, 8]
VERSION_STRING = "RBUILDER_CLIENT:%d" % CLIENT_VERSIONS[-1]

class MintClient:
    def __init__(self, server):
        """
        @param server: URL to the L{mint.server.MintServer} XMLRPC interface.
        """
        self.server = ServerProxy(server)

        serverVersions = self.server.checkVersion()

        intersection = set(serverVersions) & set(CLIENT_VERSIONS)
        if not intersection:
            raise InvalidServerVersion("Invalid server version. Server accepts client "
                "versions %s, but this client only supports versions %s." % \
                (", ".join(str(x) for x in serverVersions),
                 ", ".join(str(x) for x in CLIENT_VERSIONS)))

        self.server._protocolVersion = max(intersection)

    def newExternalProject(self, name, hostname, domainname, label, url, mirror = False):
        """
        Create a new project.
        @param name: name of new project
        @param hostname: hostname for new project
        @param domainname: domain name for new project
        @param label: label of external repository
        @param url: url of external repository
        @param mirror: this repository is a mirror of an external repository
        @return: primary key of newly created project.
        """
        return self.server.newExternalProject(name, hostname, domainname,
                                              label, url, mirror)
        
    def deleteProject(self, projectId):
        """
        Delete a project
        @param projectId: The id of the project to delete
        @type projectId: C{int}
        """
        return self.server.deleteProject(projectId)
    
    def deleteProjectByName(self, hostname):
        """
        Delete a project
        @param hostname: The hostname of the project to delete
        @type hostname: C{str}
        """
        project = self.getProjectByHostname(hostname)
        return self.server.deleteProject(project.id)

    def checkAuth(self):
        """
        Check the authentication and return an Authorization object for
        the user connecting to the MintServer.
        @return: Authorization object
        @rtype: L{mint.users.Authorization}
        """
        authTuple = self.server.checkAuth()
        return users.Authorization(**authTuple)

    def pwCheck(self, user, password):
        return self.server.pwCheck(user, password)

    def getProjectByFQDN(self, fqdn):
        """
        Retrieve a Project by its fully qualified domain name.
        @param fqdn: Fully qualified domain name of the requested project
        @rtype: L{mint.projects.Project}
        @raises mint.database.ItemNotFound: project of the requested fqdn does not exist.
        """
        projectId = self.server.getProjectIdByFQDN(fqdn)
        return projects.Project(self.server, projectId)

    def getProjectByHostname(self, hostname):
        """
        Retrieve a Project by its hostname.
        @param hostname: Hostname of the requested project
        @rtype: L{mint.projects.Project}
        @raises mint.database.ItemNotFound: project of the requested hostname does not exist.
        """
        projectId = self.server.getProjectIdByHostname(hostname)
        return projects.Project(self.server, projectId)

    def getProject(self, projectId):
        """
        Retrieve a project by database id.
        @param projectId: database id of the requested project.
        @rtype: L{mint.projects.Project}
        @raises mint.database.ItemNotFound: project does not exist
        """
        return projects.Project(self.server, projectId)

    def getUser(self, userId):
        """
        Return a User object for the given userId.
        @param userId: the database id of the requested user
        @rtype: L{mint.users.User}
        """
        return users.User(self.server, userId)

    def getUserIdByName(self, username):
        """
        Fetch user id by username
        @param username: username of requested user
        @return: database id of requested user
        """
        return self.server.getUserIdByName(username)

    def getProjectsList(self):
        """
        Return a list of all registered Projects ordered by their hostname/shortname.
        """
        return self.server.getProjectsList()

    def getLabelsForProject(self, projectId,
            overrideAuth = False, newUser = '', newPass = ''):
        """
        Return label information and authorization information for a single project.
        @param projectId: the id of the project we wish to generate label/auth info from
        @param overrideAuth:  Should we use a specific user/pass combo to access this?
        @param newUser: userid to use if overrideAuth is set to True
        @param newpass: password to use if overrideAuth is set to True
        """
        return self.server.getLabelsForProject(projectId,
            overrideAuth, newUser, newPass)

    def getBuild(self, buildId):
        """
        Retrieve a L{builds.Build} object by build id.
        @param buildId: the database id of the requested build.
        @type buildId: int
        @returns: an object representing the requested build.
        @rtype: L{builds.Build}
        """
        return builds.Build(self.server, buildId)

    def getBuildFilenames(self, buildId):
        """
        Returns a list of files and related data associated with a buildId
        """
        filenames = self.server.getBuildFilenames(buildId)
        for bf in filenames:
            if 'size' in bf:
                bf['size'] = int(bf['size'])
        return filenames

    def getrAPAPassword(self, host, role):
        return self.server.getrAPAPassword(host, role)

    def setrAPAPassword(self, host, user, password, role):
        return self.server.setrAPAPassword(host, user, password, role)

    def getFileInfo(self, fileId):
        return self.server.getFileInfo(fileId)

    def getJobServerStatus(self):
         """
         Hack to get the job server status for rBuilder Appliance.
         This needs to be extended for multiple job servers.
         Don't use with rBuilder Online!
         """
         return self.server.getJobServerStatus()

    # session management
    def loadSession(self, sid):
        return self.server.loadSession(sid) or None

    def saveSession(self, sid, data):
        self.server.saveSession(sid, data)

    def deleteSession(self, sid):
        self.server.deleteSession(sid)

    def cleanupSessions(self):
        self.server.cleanupSessions()

    def addInboundMirror(self, targetProjectId, sourceLabels,
            sourceUrl, sourceAuthType='none', sourceUsername='',
            sourcePassword='', sourceEntitlement='', allLabels = False):
        return self.server.addInboundMirror(targetProjectId, sourceLabels,
                sourceUrl, sourceAuthType, sourceUsername, sourcePassword,
                sourceEntitlement, allLabels)

    def addOutboundMirror(self, sourceProjectId, targetLabels,
            allLabels = False, recurse = False, useReleases = False, id = -1):
        return self.server.addOutboundMirror(sourceProjectId, targetLabels,
                allLabels, recurse, useReleases, id)

    def setOutboundMirrorTargets(self, outboundMirrorId, updateServiceIds):
        return self.server.setOutboundMirrorTargets(outboundMirrorId,
                updateServiceIds)

    def delOutboundMirror(self, outboundMirrorId):
        return self.server.delOutboundMirror(outboundMirrorId)

    def getInboundMirrors(self):
        return self.server.getInboundMirrors()

    def getInboundMirror(self, projectId):
        return self.server.getInboundMirror(projectId)

    def editInboundMirror(self, targetProjectId, sourceLabels,
                sourceUrl, sourceAuthType, sourceUsername, sourcePassword,
                sourceEntitlement, allLabels):
        return self.server.editInboundMirror(targetProjectId, sourceLabels,
            sourceUrl, sourceAuthType, sourceUsername, sourcePassword,
            sourceEntitlement, allLabels)

    def delInboundMirror(self, inboundMirrorId):
        return self.server.delInboundMirror(inboundMirrorId)

    def getOutboundMirrors(self):
        return self.server.getOutboundMirrors()

    def getOutboundMirror(self, outboundMirrorId):
        return self.server.getOutboundMirror(outboundMirrorId)

    def getOutboundMirrorTargets(self, outboundMirrorId):
        return self.server.getOutboundMirrorTargets(outboundMirrorId)

    def getOutboundMirrorMatchTroves(self, outboundMirrorId):
        return self.server.getOutboundMirrorMatchTroves(outboundMirrorId)

    def setOutboundMirrorMatchTroves(self, outboundMirrorId, matchStringList):
        return self.server.setOutboundMirrorMatchTroves(outboundMirrorId, matchStringList)

    def setOutboundMirrorSync(self, outboundMirrorId, value):
        return self.server.setOutboundMirrorSync(outboundMirrorId, value)

    def getOutboundMirrorGroups(self, outboundMirrorId):
        return self.server.getOutboundMirrorGroups(outboundMirrorId)

    def addUpdateService(self, hostname, adminUser, adminPassword,
            description):
        return self.server.addUpdateService(hostname, adminUser,
                adminPassword, description)

    def getUpdateService(self, upsrvId):
        return self.server.getUpdateService(upsrvId)

    def editUpdateService(self, upsrvId, hostname, mirrorUser, mirrorPassword, newDesc):
        return self.server.editUpdateService(upsrvId, hostname, mirrorUser, mirrorPassword, newDesc)

    def delUpdateService(self, upsrvId):
        return self.server.delUpdateService(upsrvId)

    def getUpdateServiceList(self):
        return self.server.getUpdateServiceList()

    def getLabel(self, labelId):
        return self.server.getLabel(labelId)

    def isLocalMirror(self, projectId):
        return self.server.isLocalMirror(projectId)

    def getAllProjectLabels(self, projectId):
        return self.server.getAllProjectLabels(projectId)

    def getProductVersion(self, versionId):
        return self.server.getProductVersion(versionId)

    def getProductVersionListForProduct(self, projectId):
        return self.server.getProductVersionListForProduct(projectId)

    def getProductVersionProdDefLabel(self, versionId):
        return self.server.getProductVersionProdDefLabel(versionId)

    def newBuildsFromProductDefinition(self, versionId, stage, force,
            buildNames = None, versionSpec = None):
        buildNames = buildNames or []
        versionSpec = versionSpec or ''
        return self.server.newBuildsFromProductDefinition(versionId, stage,
                                                          force, buildNames,
                                                          versionSpec)

    def getAllBuildsByType(self, buildType):
        return self.server.getAllBuildsByType(buildType)


class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return _Method(self.__request, name)


class _Method(xmlrpclib._Method):
    def __repr__(self):
        return "<mint._Method(%r)>" % (self.__name)

    def __str__(self):
        return self.__repr__()

    def __call__(self, *args):
        args = [VERSION_STRING] + list(args)
        isException, result = self.__send(self.__name, tuple(args))
        if not isException:
            return result
        else:
            self.handleError(result)

    def handleError(self, result):
        exceptionName, exceptionArgs = result
        if exceptionName in mint_error.__all__:
            cls = getattr(mint_error, exceptionName)
            raise cls.thaw(exceptionArgs)
        elif exceptionName in rest_error.__all__:
            cls = getattr(rest_error, exceptionName)
            raise cls.thaw(exceptionArgs)
        else:
            raise mint_error.UnknownException(exceptionName, exceptionArgs)

def upstream(version):
    """
    Returns the upstream portion of a given version, stripping off the source and build counts.
    @param version: the full version object
    @type version: L{conary.versions.Version}
    @rtype: str
    """
    return version.trailingRevision().asString().split('-')[0]

def flavorWrap(f):
    return str(f).replace(",", ", ")

def timeDelta(t, currentTime=0, capitalized=True):
    if not t:
        if capitalized:
            return "Never"
        else:
            return "never"
    curTime = currentTime
    if not currentTime:
	 curTime = time.time()
    timeOffset = time.timezone + 3600 * (time.localtime()[-1])
    days = int((curTime - timeOffset) / 86400) - int((t - timeOffset) / 86400)
    if not days:
        delta = int(curTime - t)
        if delta < 3600:
            if delta < 60:
                if not delta:
                    if capitalized:
                        return "This very second"
                    else:
                        return "this very second"
                r = str(delta) + " second"
                if (delta) != 1:
                    r +="s"
                return r + " ago"
            r = str(delta / 60) + " minute"
            if (delta / 60) != 1:
                r +="s"
            return r + " ago"
        else:
            r = str(delta / 3600) + " hour"
            if (delta / 3600) != 1:
                r +="s"
            return r + " ago"
    if days == 1:
        if capitalized:
            return 'Yesterday'
        else:
            return 'yesterday'
    if days > 1 and days < 28:
        return '%d days ago' % days
    return time.strftime('%d-%b-%Y', time.localtime(t))

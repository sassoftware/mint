#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import base64
import time
import StringIO
import xmlrpclib

from mint import builds
from mint import ec2
from mint.db import jobs
from mint import mint_error
from mint.rest import errors as rest_error
from mint import projects
from mint import pubreleases
from mint import users
from mint import packagecreator
from mint.mint_error import *

from rpath_proddef import api1 as proddef

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

    def newProject(self, name, hostname, domainname, projecturl = "", desc = "",
                   appliance = "unknown", shortname="", namespace="", 
                   prodtype="",  version="", commitEmail="", isPrivate=False,
                   projectLabel=""):
        """
        Create a new project.
        @param name: name of new project
        @param hostname: hostname for new project
        @param domainname: domain name for new project
        @param projecturl: project url for home page of new project
        @param desc: description of new project
        @param appliance: whether or not this project represents a
               a software appliance ('yes', 'no', 'unknown')
        @param shortname: the shortname of the product being created
        @param namespace: for rBuilder Online, the namespace to use in the
               first Product Version, not relevant for rBA
        @param prodtype: the type of product being created.
        @param version:  the initial product version.
        @param commitEmail: email address to which commit messages are sent.
        @param isPrivate: whether or not this should be a private product
        @param platformLabel: label of the platform to which this product
               is going to be derived from.
        @return: primary key of newly created project.
        """
        return self.server.newProject(name, hostname, domainname, projecturl, 
                                      desc, appliance, shortname, namespace, 
                                      prodtype, version, commitEmail, isPrivate,
                                      projectLabel)

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

    def updateAccessedTime(self, userId):
        return self.server.updateAccessedTime(userId)

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

    def getProjectsByMember(self, userId):
        """
        Return a list of Project objects of which the provided user is a member.
        @param userId: database id of the requested user
        @rtype: list of L{mint.projects.Project}
        """
        return [(projects.Project(self.server, x[0]['projectId'], initialData=x[0]), x[1], x[2]) for x in self.server.getProjectDataByMember(userId)]

    def getUser(self, userId):
        """
        Return a User object for the given userId.
        @param userId: the database id of the requested user
        @rtype: L{mint.users.User}
        """
        return users.User(self.server, userId)

    def getMembership(self, userId, projectId):
        """
        Returns the membership level of a user for a project, if any.
        @param userId: database id of the requested user
        @param projectId: database id of the requested project
        @rtype: one of L{mint.userlevels.LEVELS}
        """
        level = self.server.getUserLevel(userId, projectId)
        return (self.getUser(userId), level)

    def userHasRequested(self, projectId, userId):
        return self.server.userHasRequested(projectId, userId)

    def deleteJoinRequest(self, projectId, userId):
        return self.server.deleteJoinRequest(projectId, userId)

    def listJoinRequests(self, projectId):
        return self.server.listJoinRequests(projectId)

    def setJoinReqComments(self, projectId, comments):
        return self.server.setJoinReqComments(projectId, comments)

    def getJoinReqComments(self, projectId, userId):
        return self.server.getJoinReqComments(projectId, userId)

    def registerNewUser(self, username, password, fullName, email, displayEmail,
                blurb, active = False):
        """
        Request access for a new user.
        @param username: requested username
        @type username: str
        @param password: password for new user
        @type password: str
        @param fullName: full name of the new user
        @type fullName: str
        @param email: email address of the new user
        @type email: str
        @param displayEmail: spam-safe e-mail address
        @type displayEmail: str
        @param blurb: User bio/info/description
        @type blurb: str
        @param active: True to activate user immediately,
                       False to send a confirmation request
                       to email and require confirmation
                       before logging in.
        @type active: bool
        @returns: database id of new user
        """
        return self.server.registerNewUser(username, password, fullName, email, displayEmail, blurb, active)

    def getConfirmation(self, username):
        return self.server.getConfirmation(username)

    def confirmUser(self, confirmId):
        """
        Check a provided confirmation code against the database of pending new users.
        @param confirmId: confirmation code
        """
        return self.server.confirmUser(confirmId)

    def removeUserAccount(self, userId):
        """
        Remove a user account without prejudigous.
        @param userId: User account id
        """
        return self.server.removeUserAccount(userId)

    def isUserAdmin(self, userId):
        """
        Checks to see if a given user has administrative privileges.
        @param userId: the userId to check
        @return: True if the user whose id is userId is an admin
        """
        return self.server.isUserAdmin(userId)

    def getUserIdByName(self, username):
        """
        Fetch user id by username
        @param username: username of requested user
        @return: database id of requested user
        """
        return self.server.getUserIdByName(username)

    def getUserSearchResults(self, terms, limit = 10, offset = 0):
        """
        Collect the results from a users search as requested by the search
        terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.server.searchUsers(terms, limit, offset)

    def addProjectRepositoryUser(self, projectId, username, password):
        """
        Add a user to a project's conary repository.
        @param projectId: project Id.
        @type projectId: C{int}
        @param username: Username to add.
        @type username: C{string}
        @param password: Password for username.
        @type password: C{string}
        """
        return self.server.addProjectRepositoryUser(projectId, username, password)

    def getProjectSearchResults(self, terms, modified = 0, limit = 10, offset = 0, byPopularity = True, filterNoDownloads = False):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param modified: int, see searcher.py for a list of values
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @param byPopularity: if True, order items by popularity metric
        @return:       dictionary of Items requested
        """
        return self.server.searchProjects(terms, modified, limit, offset, byPopularity, filterNoDownloads)

    def getPackageSearchResults(self, terms, limit = 10, offset = 0):
        """
        Collect the results from a package search as requested by the search
        terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.server.searchPackages(terms, limit, offset)

    def getProjectsList(self):
        """
        Return a list of all registered Projects ordered by their hostname/shortname.
        """
        return self.server.getProjectsList()

    def getNewProjects(self, limit, showFledgling):
        """
        Return a list of newest projects
        @param limit:     Number of items to return
        @param showFledgling: Boolean to show fledgling (empty) projects or not.
        """
        return self.server.getNewProjects(limit, showFledgling)

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

    def getAllLabelsForProjects(self,
            overrideAuth = False, newUser = '', newPass = ''):
        """
        Return label information and authorization information for a single project.
        @param overrideAuth:  Should we use a specific user/pass combo to access this?
        @param newUser: userid to use if overrideAuth is set to True
        @param newpass: password to use if overrideAuth is set to True
        """
        return self.server.getAllLabelsForProjects(overrideAuth,
                newUser, newPass)

    def getUsers(self, sortOrder, limit, offset):
        """
        Return a list of users unfiltered in any way
        @param sortOrder: Order in which to sort the results
        @param limit:     Number of items to return
        @param offset:    Begin listing at this offset
        @return a list of user ids and a count of the total number of users
        """
        return self.server.getUsers(sortOrder, limit, offset)

    def hideProject(self, projectId):
        """
        Mark a project as hidden so that it doesn't show up in any listing,
        and is not accessible except by developers and owners of the project
        """
        return self.server.hideProject(projectId)

    def unhideProject(self, projectId):
        """
        Mark a project previously hidden as unhidden so that it shows up in
        browse and search listings, and becomes accessible through all other
        access methods, and not just to project developers and owners.
        """
        return self.server.unhideProject(projectId)
    
    def setProductVisibility(self, projectId, makePrivate):
        """
        Set the visibility of a product
        @param projectId: the project id
        @type  projectId: C{int}
        @param makePrivate: True to make private, False to make public
        @type  makePrivate: C{bool}
        @raise PermissionDenied: if not the product owner
        @raise PublicToPrivateConversionError: if trying to convert a public
               product to private
        """
        return self.server.setProductVisibility(projectId, makePrivate)

    def getAvailableBuildTypes(self):
        return self.server.getAvailableBuildTypes()

    def getBuild(self, buildId):
        """
        Retrieve a L{builds.Build} object by build id.
        @param buildId: the database id of the requested build.
        @type buildId: int
        @returns: an object representing the requested build.
        @rtype: L{builds.Build}
        """
        return builds.Build(self.server, buildId)

    def newBuild(self, projectId, buildName):
        """
        Create a new build.
        @param projectId: the project to be associated with the new build.
        @param buildName: name of the new build
        @returns: an object representing the new build
        @rtype: L{mint.builds.Build}
        """
        buildId = self.server.newBuild(projectId, buildName)
        return self.getBuild(buildId)

    def createPackageTmpDir(self):
        """
        Create a new temporary location for storing package data
        @returns: an ID that uniquely references this temporary location
        @rtype: str
        """
        return self.server.createPackageTmpDir()

    def _filterFactories(self, factories):
        """
            Converts the return value from the server (which passes an xmlblob)
            to an object tree
        """
        from pcreator import factorydata
        #Factories comes across as an xml file, need to parse that to something useable
        return [(x[0], factorydata.FactoryDefinition(fromStream=StringIO.StringIO(x[1])), x[2]) for x in factories]

    def getPackageFactories(self, projectId, uploadDirectoryHandle, versionId, sessionHandle='', upload_url='', label=''):
        """
        Upload the file referred to by id, or upload_url and pass it to the package creator service with the context from the product definition stored for C{versionId}.
        @param projectId: Project ID
        @type projectId: int
        @param id: ID returned from L{createPackageTmpDir}
        @type id: str
        @param versionId: ID of the version chosen
        @type versionId: int
        @param sessionHandle: A sessionHandle.  If empty, one will be created (and returned)
        @type sessionHandle: string
        @param upload_url: URL of a package or ''.  Not currently used
        @type upload_url: str
        @param label: Stage label
        @type label: str
        @returns: L{sessionHandle} plus a tuple containing a tuple of possible factories; see the package creator service API documentation for the format, and the filehandle to use in subsequent package creator operations
        @rtype: tuple(tuple, str, dict)
        """
        sesH, factories, data = self.server.getPackageFactories(projectId, uploadDirectoryHandle, versionId, sessionHandle, upload_url, label)

        #Parse the factory data xml
        prevChoices = packagecreator.getFactoryDataFromXML(data)

        return sesH, self._filterFactories(factories), prevChoices

    def startPackageCreatorSession(self, projectId, prodVer, namespace, troveName, label):
        """See L{mint.server.startPackageCreatorSession}"""
        return self.server.startPackageCreatorSession(projectId, prodVer, namespace, troveName, label)

    def getPackageCreatorRecipe(self, sesH):
        """
        This method returns a tuple of (isDefault, recipeData)

        isDefault is True if the recipe was not modified by the user
        """
        return self.server.getPackageCreatorRecipe(sesH)

    def savePackageCreatorRecipe(self, sesH, recipeData):
        """
        Save an override recipe. storing a blank string returns the recipe
        to its default state.
        """
        self.server.savePackageCreatorRecipe(sesH, recipeData)

    def getPackageFactoriesFromRepoArchive(self, projectId, prodVer, namespace, troveName, label):
        "See getPackageFactories, this method is used when you merely want to edit the interview data"
        sesH, factories, data = self.server.getPackageFactoriesFromRepoArchive(projectId, prodVer, namespace, troveName, label)

        #Parse the factory data xml
        prevChoices = packagecreator.getFactoryDataFromXML(data)

        return sesH, self._filterFactories(factories), prevChoices

    def savePackage(self, sessionHandle, factoryHandle, data, build=True, recipeContents=''):
        "See L{mint.server.MintServer.savePackage}"
        return self.server.savePackage(sessionHandle, factoryHandle, data, build, recipeContents)

    def getPackageBuildLogs(self, sessionHandle):
        '''See L{mint.server.MintServer.getPackageBuildLogs}'''
        return self.server.getPackageBuildLogs(sessionHandle)

    def getPackageCreatorPackages(self, projectId):
        '''See L{mint.server.MintServer.getPackageCreatorPackages}'''
        return self.server.getPackageCreatorPackages(projectId)

    def getProductVersionSourcePackages(self, projectId, versionId):
        """See L{mint.server.getProductVersionSourcePackages}"""
        return self.server.getProductVersionSourcePackages(projectId, versionId)

    def buildSourcePackage(self, projectId, versionId, troveName, troveVersion):
        """See L{mint.server.buildSourcePackage}"""
        return self.server.buildSourcePackage(projectId, versionId, troveName, troveVersion)

    def startApplianceCreatorSession(self, projectId, versionId,
            rebuild, stageLabel = None):
        """See L{mint.server.startApplianceCreatorSession}"""
        return self.server.startApplianceCreatorSession(projectId, versionId, rebuild, stageLabel)

    def makeApplianceTrove(self, sessionHandle):
        return self.server.makeApplianceTrove(sessionHandle)

    def addApplianceTrove(self, sessionHandle, troveSpec):
        return self.server.addApplianceTrove(sessionHandle, troveSpec)

    def addApplianceTroves(self, sessionHandle, troveList):
        return self.server.addApplianceTroves(sessionHandle, troveList)

    def setApplianceTroves(self, sessionHandle, troveList):
        return self.server.setApplianceTroves(sessionHandle, troveList)

    def listApplianceTroves(self, projectId, sessionHandle):
        return self.server.listApplianceTroves(projectId, sessionHandle)

    def addApplianceSearchPaths(self, sessionHandle, searchPaths):
        return self.server.addApplianceSearchPaths(sessionHandle, searchPaths)

    def listApplianceSearchPaths(self, sessionHandle):
        return self.server.listApplianceSearchPaths(sessionHandle)

    def removeApplianceSearchPaths(self, sessionHandle, searchPaths):
        return self.server.removeApplianceSearchPaths(sessionHandle, searchPaths)

    def getBuildFilenames(self, buildId):
        """
        Returns a list of files and related data associated with a buildId
        """
        filenames = self.server.getBuildFilenames(buildId)
        for bf in filenames:
            if 'size' in bf:
                bf['size'] = int(bf['size'])
        return filenames

    def getPublishedReleaseList(self, limit=10, offset=0):
        """
        Get a list of the most recent published releases as ordered
        by their published date.
        @param limit: The number of published releases to display
        @param offset: List @limit starting at item @offset
        """
        return [(x[0], x[1], self.getPublishedRelease(x[2])) for x in \
                self.server.getPublishedReleaseList(limit, offset)]

    def newPublishedRelease(self, projectId):
        """
        Create a new published release, which is a collection of 
        builds (images, group troves, etc.).
        @param projectId: the project to be associated with the release
        @returns: an object representing the new published release
        @rtype: L{mint.pubreleases.PublishedRelease}
        """
        pubReleaseId = self.server.newPublishedRelease(projectId)
        return self.getPublishedRelease(pubReleaseId)

    def getPublishedRelease(self, pubReleaseId):
        """
        Get a published release by its id.
        @param pubReleaseId: the id of the published release
        @returns: an object representing the published release
        @rtype: L{mint.pubreleases.PublishedRelease}
        """
        # XXX broken
        #return self.server.getPublishedRelease(pubReleaseId)
        return pubreleases.PublishedRelease(self.server, pubReleaseId)

    def deletePublishedRelease(self, pubReleaseId):
        """
        Delete a published release. This has the side effect of unlinking
        any builds associated with that release.
        @param pubReleaseId: the id of the published release
        @returns: True if successful, False otherwise
        @rtype: bool
        """
        return self.server.deletePublishedRelease(pubReleaseId)

    def publishPublishedRelease(self, pubReleaseId, shouldMirror):
        """
        Publish a published release. The release will become visible on
        the project homepage and RSS feed, and users without read
        access will be able to download the images. Depending on the
        value of I{shouldMirror}, the release may be mirrored to
        all configured Update Services.

        @param pubReleaseId: the id of the published release
        @param shouldMirror: if True, the release will be marked for
            mirroring
        @type shouldMirror: bool
        """
        return self.server.publishPublishedRelease(pubReleaseId, shouldMirror)

    def unpublishPublishedRelease(self, pubReleaseId):
        """
        Unpublish a published release. The release will no longer be
        visible on the project homepage and RSS feed, and
        unprivileged users will not be able to see the associated
        builds. If the release was marked for mirroring, it will no
        longer be mirrored, although if it has already been mirrored
        the troves will not be removed from the mirror.

        @param pubReleaseId: the id of the published release
        """
        return self.server.unpublishPublishedRelease(pubReleaseId)

    def getrAPAPassword(self, host, role):
        return self.server.getrAPAPassword(host, role)

    def setrAPAPassword(self, host, user, password, role):
        return self.server.setrAPAPassword(host, user, password, role)

    def startImageJob(self, buildId):
        """
        Start a new image generation job.
        @param buildId: the build id which describes the image to be created.
        @return: the unique identifier of the job
        @rtype: C{str}
        """
        return self.server.startImageJob(buildId)

    def addDownloadHit(self, urlId, ip):
        return self.server.addDownloadHit(urlId, ip)

    def getFileInfo(self, fileId):
        return self.server.getFileInfo(fileId)

    def promoteUserToAdmin(self, userId):
        """
        Promotes a user to an administrator.
        @param userId: the userId to promote
        """
        return self.server.promoteUserToAdmin(userId)

    def demoteUserFromAdmin(self, userId):
         """
         Demotes a user from administrator.
         @param userId: the userId to promote
         """
         return self.server.demoteUserFromAdmin(userId)

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

    # report functions
    def listAvailableReports(self):
        return self.server.listAvailableReports()

    def getReportPdf(self, name):
        return base64.b64decode(self.server.getReportPdf(name))

    def getReport(self, name):
        return self.server.getReport(name)

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

    def isProjectMirroredByRelease(self, projectId):
        '''
        Returns True if the given project is configured for outbound
        mirroring and is using "mirror by release".

        @param projectId: id of project to check
        '''
        return self.server.isProjectMirroredByRelease(projectId)

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

    def getBuildsForPublishedRelease(self, pubReleaseId):
        return self.server.getBuildsForPublishedRelease(pubReleaseId)

    def getMirrorableReleasesByProject(self, projectId):
        return self.server.getMirrorableReleasesByProject(projectId)

    def addUpdateService(self, hostname, adminUser, adminPassword,
            description):
        return self.server.addUpdateService(hostname, adminUser,
                adminPassword, description)

    def getUpdateService(self, upsrvId):
        return self.server.getUpdateService(upsrvId)

    def editUpdateService(self, upsrvId, newDesc):
        return self.server.editUpdateService(upsrvId, newDesc)

    def delUpdateService(self, upsrvId):
        return self.server.delUpdateService(upsrvId)

    def getUpdateServiceList(self):
        return self.server.getUpdateServiceList()

    def getLabel(self, labelId):
        return self.server.getLabel(labelId)

    def isLocalMirror(self, projectId):
        return self.server.isLocalMirror(projectId)

    def getTroveReferences(self, troveName, troveVersion, troveFlavors = []):
        return dict(self.server.getTroveReferences(troveName, troveVersion, troveFlavors))

    def getTroveDescendants(self, troveName, troveLabel, troveFlavor):
        return dict(self.server.getTroveDescendants(troveName, troveLabel, troveFlavor))

    def validateEC2Credentials(self, authToken):
        return self.server.validateEC2Credentials(authToken)
    
    def getEC2KeyPair(self, authToken, keyName):
        return self.getEC2KeyPairs(authToken, [keyName])
    
    def getEC2KeyPairs(self, authToken, keyNames):
        return self.server.getEC2KeyPairs(authToken, keyNames)

    def getFullRepositoryMap(self):
        return self.server.getFullRepositoryMap()

    def getAllProjectLabels(self, projectId):
        return self.server.getAllProjectLabels(projectId)

    def setBuildFilenamesSafe(self, buildId, outputToken, filenames):
        for f in filenames:
            if len(f) == 4:
                f[2] = str(f[2])
        return self.server.setBuildFilenamesSafe(buildId, outputToken,
                filenames)

    def setBuildAMIDataSafe(self, buildId, outputToken, amiId, amiManifestName):
        return self.server.setBuildAMIDataSafe(buildId, outputToken,
                amiId, amiManifestName)

    def addProductVersion(self, projectId, namespace, name, description=''):
        return self.server.addProductVersion(projectId, namespace, name,
                                             description)

    def getProductVersion(self, versionId):
        return self.server.getProductVersion(versionId)

    def getStagesForProductVersion(self, versionId):
        return self.server.getStagesForProductVersion

    def getProductDefinitionForVersion(self, versionId):
        pdXMLString = self.server.getProductDefinitionForVersion(versionId)
        return proddef.ProductDefinition(fromStream=pdXMLString)

    def setProductDefinitionForVersion(self, versionId, productDefinition,
            rebaseToPlatformLabel=None):
        sio = StringIO.StringIO()
        productDefinition.serialize(sio)
        if not rebaseToPlatformLabel: rebaseToPlatformLabel = ''
        return self.server.setProductDefinitionForVersion(versionId, sio.getvalue(),
                rebaseToPlatformLabel)

    def editProductVersion(self, versionId, newDesc):
        return self.server.editProductVersion(versionId, newDesc)

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
        
    def getBuildTaskListForDisplay(self, versionId, stageName):
        return self.server.getBuildTaskListForDisplay(versionId, stageName)

    def getEC2CredentialsForUser(self, userId):
        return self.server.getEC2CredentialsForUser(userId)

    def setEC2CredentialsForUser(self, userId, awsAccountNumber,
            awsPublicAccessKeyId, awsSecretAccessKey, force):
        return self.server.setEC2CredentialsForUser(userId,
                awsAccountNumber, awsPublicAccessKeyId,
                awsSecretAccessKey, force)

    def addTarget(self, targetType, targetName, dataDict):
        return self.server.addTarget(targetType, targetName, dataDict)

    def deleteTarget(self, targetType, targetName):
        return self.server.deleteTarget(targetType, targetName)

    def removeEC2CredentialsForUser(self, userId):
        return self.server.removeEC2CredentialsForUser(userId)

    def getTargetData(self, targetType, targetName):
        return self.server.getTargetData(targetType, targetName)

    def getAMIBuildsForUser(self, userId):
        return self.server.getAMIBuildsForUser(userId)

    def getAllBuildsByType(self, buildType):
        return self.server.getAllBuildsByType(buildType)

    def getAvailablePackages(self, sessionHandle, refresh = False):
        from conary import versions as conaryver
        from conary.deps import deps as conarydeps
        pkgs = self.server.getAvailablePackages(sessionHandle, refresh)
        ret = []
        for label in pkgs:
            ret.append([(x[0],
                conaryver.ThawVersion(str(x[1])),
                conarydeps.ThawFlavor(str(x[2]))) for x in label])
        return ret
        
    def getAvailablePackagesFiltered(self, sessionHandle, refresh = False, ignoreComponents = True):
        return self.server.getAvailablePackagesFiltered(sessionHandle, refresh, ignoreComponents)

    def getAvailablePlatforms(self):
        return self.server.getAvailablePlatforms()

    def isPlatformAcceptable(self, platformLabel):
        return self.server.isPlatformAcceptable(platformLabel)

    def isPlatformAvailable(self, platformLabel):
        return self.server.isPlatformAvailable(platformLabel)

    def getProxies(self):
        return self.server.getProxies()

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

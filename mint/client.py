#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All rights reserved
#
import base64
import os
import sys
import time
import xmlrpclib

from mint import database
from mint import ec2
from mint import grouptrove
from mint import jobs
from mint import projects
from mint import builds
from mint import pubreleases
from mint import users
from mint import rmakebuild
from mint.mint_error import *
from mint.searcher import SearchTermsError

from conary.repository import repository
from conary.repository.netclient import UserNotFound
from conary.deps import deps

CLIENT_VERSIONS = [4]
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

    def newProject(self, name, hostname, domainname, projecturl = "", desc = "", appliance = "unknown"):
        """
        Create a new project.
        @param name: name of new project
        @param hostname: hostname for new project
        @param domainname: domain name for new project
        @param projecturl: project url for home page of new project
        @param desc: description of new project
        @param appliance: whether or not this project represents a
               a software appliance ('yes', 'no', 'unknown')
        @return: primary key of newly created project.
        """
        return self.server.newProject(name, hostname, domainname, projecturl, desc, appliance)

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
        return [(projects.Project(self.server, x[0]), x[1]) for x in self.server.getProjectIdsByMember(userId)]

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

    def getUsersList(self):
        """
        Fetch users and IDs
        """
        return self.server.getUsersList()

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
        return self.server.getLabelsForProject(projectId,
            overrideAuth, newUser, newPass)

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

    def newBuildsFromXml(self, projectId, label, buildXml):
        """
        Create a series of new builds from xml input.
        @param projectId: the project to be associated with the new build.
        @param label: the label to associate the builds with
        @param buildXml: xml data describing the builds
        @returns: a list of objects representing the new builds
        """
        buildIds = self.server.newBuildsFromXml(projectId, label, buildXml)
        return [self.getBuild(x) for x in buildIds]

    def commitBuildXml(self, projectId, label, buildXml):
        """
        Commit a source trove to the given label, storing the xml input.
        @param projectId: the project to be associated with the new build.
        @param label: the label to store the trove on.
        @param buildXml: xml data describing the builds
        """
        return self.server.commitBuildXml(projectId, label, buildXml)

    def checkoutBuildXml(self, projectId, label):
        """
        Check out a source trove from the given label, returning the build xml.
        @param projectId: the project to be associated with the new build.
        @param label: the label to store the trove on.
        @returns: a string containing xml
        """
        return self.server.checkoutBuildXml(projectId, label)


    def getBuildFilenames(self, buildId):
        """
        Returns a list of files and related data associated with a buildId
        """
        return self.server.getBuildFilenames(buildId)

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

    def getCommunityId(self, projectId, communityType):
        return self.server.getCommunityId(projectId, communityType)

    def setCommunityId(self, projectId, communityType, communityId):
        return self.server.setCommunityId(projectId, communityType, communityId)

    def deleteCommunityId(self, projectId, communityType):
        return self.server.deleteCommunityId(projectId, communityType)

    def getrAPAPassword(self, host, role):
        return self.server.getrAPAPassword(host, role)

    def setrAPAPassword(self, host, user, password, role):
        return self.server.setrAPAPassword(host, user, password, role)

    def startImageJob(self, buildId):
        """
        Start a new image generation job.
        @param buildId: the build id which describes the image to be created.
        @return: an object representing the new job
        @rtype: L{mint.jobs.Job}
        """
        return self.server.startImageJob(buildId)

    def getJob(self, jobId):
        """
        Retrieve a L{jobs.Job} object by job id.
        @param jobId: the database id of the requested job.
        @type jobId: int
        @returns: an object representing the requested job.
        @rtype: L{jobs.Job}
        """
        raise NotImplementedError
        return jobs.Job(self.server, jobId)

    def listActiveJobs(self, filter):
        """List the jobs in the job queue.
        @param filter: If True it will only show running or waiting jobs.
          If False it will show all jobs for past 24 hours.
        @return: list of jobIds"""
        return self.server.listActiveJobs(filter)

    def startNextJob(self, archTypes, jobTypes, jobServerVersion):
        jobId = self.server.startNextJob(archTypes, jobTypes, jobServerVersion)
        if jobId:
            return self.getJob(jobId)
        return None

    def getJobs(self):
        """
        Iterates through all jobs.
        @returns: list jobs found
        @rtype: list of L{jobs.Job}s
        """
        return [self.getJob(x) for x in self.server.getJobIds()]

    def addDownloadHit(self, urlId, ip):
        return self.server.addDownloadHit(urlId, ip)

    def getFileInfo(self, fileId):
        return self.server.getFileInfo(fileId)

    def getNews(self):
        """
        Return a list of news items from the RSS news cache.
        @return: list of news item dictionaries
        """
        return self.server.getNews()

    def getNewsLink(self):
        """
        Returns the web URL of the news RSS feed.
        @return: web URL
        """
        return self.server.getNewsLink()

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

    def translateProjectFQDN(self, fqdn):
        return self.server.translateProjectFQDN(fqdn)

    # session management
    def loadSession(self, sid):
        return self.server.loadSession(sid) or None

    def saveSession(self, sid, data):
        self.server.saveSession(sid, data)

    def deleteSession(self, sid):
        self.server.deleteSession(sid)

    def cleanupSessions(self):
        self.server.cleanupSessions()

    # group trove functions
    def createGroupTrove(self, projectId, recipeName, upstreamVersion,
                         desc, autoResolve):
        groupTroveId = self.server.createGroupTrove(projectId, recipeName,
                                                    upstreamVersion,
                                                    desc, autoResolve)
        return self.getGroupTrove(groupTroveId)

    def deleteGroupTrove(self, groupTroveId):
        return self.server.deleteGroupTrove(groupTroveId)

    def getGroupTrove(self, groupTroveId):
        return grouptrove.GroupTrove(self.server, groupTroveId)

    def listGroupTrovesByProject(self, projectId):
        return self.server.listGroupTrovesByProject(projectId)

    # rMake build functions
    def getrMakeBuild(self, rMakeBuildId):
        return rmakebuild.rMakeBuild(self.server, rMakeBuildId)

    def getrMakeBuildTrove(self, rMakeBuildItemId):
        return self.server.getrMakeBuildTrove(rMakeBuildItemId)

    def delrMakeBuildTrove(self, rMakeBuildItemId):
        return self.server.delrMakeBuildTrove(rMakeBuildItemId)

    def createrMakeBuild(self, title):
        return self.getrMakeBuild(self.server.createrMakeBuild(title))

    def setrMakeBuildStatus(self, UUID, status, statusMessage):
        return self.server.setrMakeBuildStatus(UUID, status, statusMessage)

    def listrMakeBuilds(self):
        return sorted([self.getrMakeBuild(x) for x in \
                       self.server.listrMakeBuilds()], key = lambda x:x.title)

    # report functions
    def listAvailableReports(self):
        return self.server.listAvailableReports()

    def getReportPdf(self, name):
        return base64.b64decode(self.server.getReportPdf(name))

    def getReport(self, name):
        return self.server.getReport(name)

    def getDownloadChart(self, projectId, days, format = 'png'):
        return self.server.getDownloadChart(projectId, days, format)

    def addInboundMirror(self, targetProjectId, sourceLabels,
            sourceUrl, sourceUsername, sourcePassword, allLabels = False):
        return self.server.addInboundMirror(targetProjectId, sourceLabels,
                sourceUrl, sourceUsername, sourcePassword, allLabels)

    def addOutboundMirror(self, sourceProjectId, targetLabels,
            allLabels = False, recurse = False):
        return self.server.addOutboundMirror(sourceProjectId, targetLabels,
                allLabels, recurse)

    def addOutboundMirrorTarget(self, outboundMirrorId, targetUrl,
            mirroruser, mirrorpass):
        return self.server.addOutboundMirrorTarget(outboundMirrorId,
                targetUrl, mirroruser, mirrorpass)

    def delOutboundMirrorTarget(self, outboundMirrorTargetId):
        return self.server.delOutboundMirrorTarget(outboundMirrorTargetId)

    def delOutboundMirror(self, outboundMirrorId):
        return self.server.delOutboundMirror(outboundMirrorId)

    def getInboundMirrors(self):
        return self.server.getInboundMirrors()

    def getInboundMirror(self, projectId):
        return self.server.getInboundMirror(projectId)

    def editInboundMirror(self, targetProjectId, sourceLabels,
                sourceUrl, sourceUsername, sourcePassword, allLabels):
        return self.server.editInboundMirror(targetProjectId, sourceLabels,
            sourceUrl, sourceUsername, sourcePassword, allLabels)

    def delInboundMirror(self, inboundMirrorId):
        return self.server.delInboundMirror(inboundMirrorId)

    def getOutboundMirrors(self):
        return self.server.getOutboundMirrors()

    def getOutboundMirror(self, outboundMirrorId):
        return self.server.getOutboundMirror(outboundMirrorId)

    def getOutboundMirrorTarget(self, outboundMirrorTargetId):
        return self.server.getOutboundMirrorTarget(outboundMirrorTargetId)

    def getOutboundMirrorTargets(self, outboundMirrorId):
        return self.server.getOutboundMirrorTargets(outboundMirrorId)

    def getOutboundMirrorMatchTroves(self, outboundMirrorId):
        return self.server.getOutboundMirrorMatchTroves(outboundMirrorId)

    def setOutboundMirrorMatchTroves(self, outboundMirrorId, matchStringList):
        return self.server.setOutboundMirrorMatchTroves(outboundMirrorId, matchStringList)

    def getLabel(self, labelId):
        return self.server.getLabel(labelId)

    def isLocalMirror(self, projectId):
        return self.server.isLocalMirror(projectId)

    def addRemappedRepository(self, fromName, toName):
        return self.server.addRemappedRepository(fromName, toName)

    def delRemappedRepository(self, fromName):
        return self.server.delRemappedRepository(fromName)

    def getUseItIcons(self):
        return self.server.getUseItIcons()

    def deleteUseItIcon(self, itemId):
        return self.server.deleteUseItIcon(itemId)

    def addUseItIcon(self, itemId, name, link):
        return self.server.addUseItIcon(itemId, name, link)

    def getCurrentSpotlight(self):
        return self.server.getCurrentSpotlight()

    def getSpotlightAll(self):
        return self.server.getSpotlightAll()

    def addSpotlightItem(self, title, text, link, logo, showArchive, startDate,
                         endDate):
         return self.server.addSpotlightItem(title, text, link, logo,
                                             showArchive, startDate, endDate)

    def deleteSpotlightItem(self, itemId):
        return self.server.deleteSpotlightItem(itemId)

    def addFrontPageSelection(self, name, link, rank):
        return self.server.addFrontPageSelection(name, link, rank)

    def deleteFrontPageSelection(self, itemId):
        return self.server.deleteFrontPageSelection(itemId)

    def getFrontPageSelection(self):
        return self.server.getFrontPageSelection()

    def getTopProjects(self):
        return self.server.getTopProjects()

    def getPopularProjects(self):
        return self.server.getPopularProjects()

    def getTroveReferences(self, troveName, troveVersion, troveFlavors = []):
        return dict(self.server.getTroveReferences(troveName, troveVersion, troveFlavors))

    def getTroveDescendants(self, troveName, troveLabel, troveFlavor):
        return dict(self.server.getTroveDescendants(troveName, troveLabel, troveFlavor))

    # ec2 "try it now" support
    def createBlessedAMI(self, ec2AMIId, shortDescription):
        return self.server.createBlessedAMI(ec2AMIId, shortDescription)

    def getBlessedAMI(self, blessedAMIId):
        return ec2.BlessedAMI(self.server, blessedAMIId)

    def getAvailableBlessedAMIs(self):
        return [self.getBlessedAMI(x) for x in \
                self.server.getAvailableBlessedAMIs()]

    def getLaunchedAMI(self, launchedAMIId):
        return ec2.LaunchedAMI(self.server, launchedAMIId)

    def getActiveLaunchedAMIs(self):
        return [self.getLaunchedAMI(x) for x in \
                self.server.getActiveLaunchedAMIs()]

    def getLaunchedAMIInstanceStatus(self, launchedAMIId):
        return self.server.getLaunchedAMIInstanceStatus(launchedAMIId)

    def launchAMIInstance(self, blessedAMIId):
        return self.server.launchAMIInstance(blessedAMIId)

    def terminateExpiredAMIInstances(self):
        return self.server.terminateExpiredAMIInstances()

    def extendLaunchedAMITimeout(self, launchedAMIId):
        return self.server.extendLaunchedAMITimeout(launchedAMIId)

    def checkHTTPReturnCode(self, uri, expectedCodes=[200, 301, 302]):
        return self.server.checkHTTPReturnCode(uri, expectedCodes)

    def getFullRepositoryMap(self):
        return self.server.getFullRepositoryMap()

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
        exceptionName = result[0]
        exceptionArgs = result[1:]

        if exceptionName == "UserAlreadyExists":
            raise users.UserAlreadyExists
        elif exceptionName == "DuplicateItem":
            raise database.DuplicateItem(exceptionArgs[0])
        elif exceptionName == "DuplicateHostname":
            raise projects.DuplicateHostname()
        elif exceptionName == "DuplicateName":
            raise projects.DuplicateName()
        elif exceptionName == "ItemNotFound":
            raise database.ItemNotFound(exceptionArgs[0])
        elif exceptionName == "FileMissing":
            raise FileMissing(exceptionArgs[0])
        elif exceptionName == "MethodNotSupported":
            raise MethodNotSupported(exceptionArgs[0])
        elif exceptionName == "SearchTermsError":
            raise SearchTermsError(exceptionArgs[0])
        elif exceptionName == "AlreadyConfirmed":
            raise users.AlreadyConfirmed(exceptionArgs[0])
        elif exceptionName == "GroupAlreadyExists":
            raise users.GroupAlreadyExists(exceptionArgs[0])
        elif exceptionName == "InvalidHostname":
            raise projects.InvalidHostname(exceptionArgs[0])
        elif exceptionName == "MailError":
            raise users.MailError(exceptionArgs[0])
        elif exceptionName == "DuplicateJob":
            raise jobs.DuplicateJob(exceptionArgs[0])
        elif exceptionName == "OpenError":
            raise repository.OpenError(exceptionArgs[0])
        elif exceptionName == "PermissionDenied":
            raise PermissionDenied(exceptionArgs[0])
        elif exceptionName == "LastOwner":
            raise users.LastOwner(exceptionArgs[0])
        elif exceptionName == "UserInduction":
            raise users.UserInduction(exceptionArgs[0])
        elif exceptionName == "UserNotFound":
            raise UserNotFound(exceptionArgs[0])
        elif exceptionName == "BuildPublished":
            raise BuildPublished(exceptionArgs[0])
        elif exceptionName == "BuildMissing":
            raise BuildMissing(exceptionArgs[0])
        elif exceptionName == "BuildEmpty":
            raise BuildEmpty(exceptionArgs[0])
        elif exceptionName == "AuthRepoError":
            raise users.AuthRepoError(exceptionArgs[0])
        elif exceptionName == "LabelMissing":
            raise projects.LabelMissing(exceptionArgs[0])
        elif exceptionName == "UserAlreadyAdmin":
            raise UserAlreadyAdmin(exceptionArgs[0])
        elif exceptionName == "AdminSelfDemotion":
            raise AdminSelfDemotion(exceptionArgs[0])
        elif exceptionName == "JobserverVersionMismatch":
            raise JobserverVersionMismatch(exceptionArgs[0])
        elif exceptionName == "MaintenanceMode":
            raise MaintenanceMode(exceptionArgs[0])
        elif exceptionName == "LastOwner":
            raise users.LastOwner(exceptionArgs[0])
        elif exceptionName == "ParameterError":
            raise ParameterError(exceptionArgs[0])
        else:
            raise UnknownException(exceptionName, exceptionArgs)

class MethodNotSupported(MintError):
    def __init__(self, method):
        self.method = method

    def __str__(self):
        return "method not supported by XMLRPC server: %s" % self.method

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

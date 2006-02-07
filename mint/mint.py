#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import os
import sys
import xmlrpclib
import textwrap
import time

from conary.repository import repository
from conary.repository.netclient import UserNotFound
from conary.deps import deps

import database
import jobs
import projects
import releases
import users
import grouptrove
import base64
from mint_error import MintError, UnknownException, PermissionDenied, \
    ReleasePublished, ReleaseMissing, ReleaseEmpty
from searcher import SearchTermsError


class MintClient:
    def __init__(self, server):
        """
        @param server: URL to the L{mint.mint_server.MintServer} XMLRPC interface.
        """
        self.server = ServerProxy(server)

    def newProject(self, name, hostname, domainname, projecturl = "", desc = ""):
        """
        Create a new project.
        @param name: name of new project
        @param hostname: hostname for new project
        @param desc: description of new project
        @return: primary key of newly created project.
        """
        return self.server.newProject(name, hostname, domainname, projecturl, desc)

    def checkAuth(self):
        """
        Check the authentication and return an Authorization object for
        the user connecting to the MintServer.
        @return: Authorization object
        @rtype: L{mint.users.Authorization}
        """
        authTuple = self.server.checkAuth()
        return users.Authorization(**authTuple)

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

    def getProjectSearchResults(self, terms, modified = 0, limit = 10, offset = 0):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param modified: int, see searcher.py for a list of values
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.server.searchProjects(terms, modified, limit, offset)

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

    def getProjects(self, sortOrder, limit, offset):
        """
        Return a list of projects unfiltered in any way
        @param sortOrder: Order in which to sort the results
        @param limit:     Number of items to return
        @param offset:    Begin listing at this offset
        """
        return self.server.getProjects(sortOrder, limit, offset)

    def getUsers(self, sortOrder, limit, offset):
        """
        Return a list of users unfiltered in any way
        @param sortOrder: Order in which to sort the results
        @param limit:     Number of items to return
        @param offset:    Begin listing at this offset
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

    def disableProject(self, projectId):
        """
        Mark a project as disabled so that it doesn't show up in any listing, 
        and is not accessible via any other access method.
        """
        return self.server.disableProject(projectId)

    def enableProject(self, projectId):
        """
        Mark a project previously disabled as enabled so that it shows up in
        browse and search listings, and becomes accessible through all other
        access methods.
        """
        return self.server.enableProject(projectId)

    def getRelease(self, releaseId):
        """
        Retrieve a L{releases.Release} object by release id.
        @param releaseId: the database id of the requested release.
        @type releaseId: int
        @returns: an object representing the requested release.
        @rtype: L{releases.Release}
        """
        return releases.Release(self.server, releaseId)

    def newRelease(self, projectId, releaseName, published = False):
        """
        Create a new release.
        @param projectId: the project to be associated with the new release.
        @param releaseName: name of the new release
        @returns: an object representing the new release
        @rtype: L{mint.releases.Release}
        """
        releaseId = self.server.newRelease(projectId, releaseName, published) 
        return self.getRelease(releaseId)

    def getReleaseList(self, limit=10, offset=0):
        """
        Get a list of the most recent releases as ordered by their published date.
        @param limit: The number of releases to display
        @param offset: List @limit starting at item @offset
        """
        return self.server.getReleaseList(limit, offset)

    def startImageJob(self, releaseId):
        """
        Start a new image generation job.
        @param releaseId: the release id which describes the image to be created.
        @return: an object representing the new job
        @rtype: L{mint.jobs.Job}
        """
        jobId = self.server.startImageJob(releaseId)
        return self.getJob(jobId)

    def getJob(self, jobId):
        """
        Retrieve a L{jobs.Job} object by job id.
        @param jobId: the database id of the requested job.
        @type jobId: int
        @returns: an object representing the requested job.
        @rtype: L{jobs.Job}
        """
        return jobs.Job(self.server, jobId)

    def startNextJob(self, archTypes, jobTypes):
        jobId = self.server.startNextJob(archTypes, jobTypes)
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

    def notifyUsers(self, subject, body):
        """
        Send a message with the subject and body specified to all registered
        members using their confirmed e-mail address.
        """
        return self.server.notifyUsers(subject, body)

    # session management
    def loadSession(self, sid):
        return self.server.loadSession(sid)

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

    # report functions
    def listAvailableReports(self):
        return self.server.listAvailableReports()

    def getReportPdf(self, name):
        return base64.b64decode(self.server.getReportPdf(name))

    # label functions
    def versionIsExternal(self, versionStr):
        return self.server.versionIsExternal(versionStr)

class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return _Method(self.__request, name)

class _Method(xmlrpclib._Method):
    def __repr__(self):
        return "<mint._Method(%r)>" % (self.__name)

    def __str__(self):
        return self.__repr__()

    def __call__(self, *args):
        isException, result = self.__send(self.__name, args)
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
            raise jobs.FileMissing(exceptionArgs[0])
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
        elif exceptionName == "ReleasePublished":
            raise ReleasePublished(exceptionArgs[0])
        elif exceptionName == "ReleaseMissing":
            raise ReleaseMissing(exceptionArgs[0])
        elif exceptionName == "ReleaseEmpty":
            raise ReleaseEmpty(exceptionArgs[0])
        elif exceptionName == "AuthRepoError":
            raise users.AuthRepoError(exceptionArgs[0])
        elif exceptionName == "LabelMissing":
            raise projects.LabelMissing(exceptionArgs[0])
        else:
            raise UnknownException(exceptionName, exceptionArgs)

class MethodNotSupported(MintError):
    def __init__(self, method):
        self.method = method

    def __str__(self):
        return "method not supported by XMLRPC server: %s" % self.method

def extractIs(flavor):
    """
    Returns just the instruction set of a given flavor.
    @param flavor: the full flavor
    @type flavor: L{conary.deps.deps.DependencySet}
    @rtype: str
    """
    return flavor.members[deps.DEP_CLASS_IS].members.keys()[0]

def upstream(version):
    """
    Returns the upstream portion of a given version, stripping off the source and build counts.
    @param version: the full version object
    @type version: L{conary.versions.Version}
    @rtype: str
    """
    return version.trailingRevision().asString().split('-')[0]

def flavorWrap(f):
    f = str(f).replace(" ", "\n")
    f = f.replace(",", " ")
    f = f.replace("\n", "\t")
    f = textwrap.wrap(f, expand_tabs=False, replace_whitespace=False)
    return ",\n".join(x.replace(" ", ",") for x in f)

def timeDelta(t):
    if not t:
        return "Never"
    curTime = time.time()
    timeOffset = time.timezone + 3600 * (time.localtime()[-1])
    days = int((curTime - timeOffset) / 86400) - int((t - timeOffset) / 86400)
    if not days:
        delta = int(curTime - t)
        if delta < 3600:
            if delta < 60:
                if not delta:
                    return "This very second"
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
        return 'Yesterday'
    if days > 1 and days < 28:
        return '%d days ago' % days
    return time.strftime('%d-%b-%Y', time.localtime(t))

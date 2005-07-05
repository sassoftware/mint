#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import os
import sys
import xmlrpclib

import database
import jobs
import projects
import releases
import users
from mint_error import MintError

class MintClient:
    def __init__(self, server):
        """
        @param server: URL to the L{mint.mint_server.MintServer} XMLRPC interface.
        """
        self.server = ServerProxy(server)

    def newProject(self, name, hostname, desc = ""):
        """
        Create a new project.
        @param name: name of new project
        @param hostname: hostname for new project
        @param desc: description of new project
        @return: primary key of newly created project.
        """
        return self.server.newProject(name, hostname, desc)

    def checkAuth(self):
        """
        Check the authentication and return an Authorization object for
        the user connecting to the MintServer.
        @return: Authorization object
        @rtype: L{mint.users.Authorization}
        """
        authTuple = self.server.checkAuth()
        return users.Authorization(**authTuple)

    def getProjectByHostname(self, hostname):
        """
        Retrieve a Project by hostname.
        @param hostname: hostname of the requested project
        @rtype: L{mint.projects.Project}
        @raises mint.database.ItemNotFound: project of the requested hostname does not exist.
        """
        projectId = self.server.getProjectIdByHostname(hostname)
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

    def registerNewUser(self, username, password, fullName, email, active = False):
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
        @param active: True to activate user immediately,
                       False to send a confirmation request
                       to email and require confirmation
                       before logging in.
        @type active: bool
        @returns: database id of new user
        """
        return self.server.registerNewUser(username, password, fullName, email, active)

    def confirmUser(self, confirmId):
        """
        Check a provided confirmation code against the database of pending new users.
        @param confirmId: confirmation code
        """
        return self.server.confirmUser(confirmId)

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

    def getRelease(self, releaseId):
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
        return jobs.Job(self.server, jobId)
        
    def iterJobs(self, releaseId = -1):
        for jobId in self.server.getJobIds(releaseId):
            yield self.getJob(jobId)

    def getNews(self):
        """
        Return a list of news items from the RSS news cache.
        @return: list of news item dictionaries
        """
        return self.server.getNews()

class ServerProxy(xmlrpclib.ServerProxy):
    def __getattr__(self, name):
        return _Method(self.__request, name)

class _Method(xmlrpclib._Method):
    def __repr__(self):
        return "<mint._Method(%s, %r)>" % (self._Method__send, self._Method__name)

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
            raise projects.DuplicateHostname
        elif exceptionName == "ItemNotFound":
            raise database.ItemNotFound(exceptionArgs[0])
        elif exceptionName == "MethodNotSupported":
            raise MethodNotSupported(exceptionArgs[0])
        else:
            raise UnknownException(exceptionName, exceptionArgs)

class UnknownException(Exception):
    def __str__(self):
        return "%s %s" % (self.eName, self.eArgs)

    def __init__(self, eName, eArgs):
        self.eName = eName
        self.eArgs = eArgs

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

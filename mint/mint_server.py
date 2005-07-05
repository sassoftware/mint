#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import re
import sqlite3
import sys
import time

import database
import jobs
import jobstatus
import news
import projects
import releases
import versions
import users
import userlevels
from cache import TroveNamesCache
from mint_error import MintError


import repository.netrepos.netauth
from repository import netclient

from imagetool import imagetool

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'www', 'web', 'rpath', 'wiki', 'conary']

allTroveNames = TroveNamesCache()

class PermissionDenied(MintError):
    def __str__(self):
        return "permission denied"

def requiresAuth(func):
    def wrapper(self, *args):
        if not self.auth.authorized:
            raise PermissionDenied
        else:
            return func(self, *args)
    return wrapper

class MintServer(object):
    _checkRepo = True 
    def callWrapper(self, methodName, authToken, args):
        if methodName.startswith('_'):
            raise AttributeError
        try:
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            # check authorization
            auth = self.users.checkAuth(authToken, checkRepo = self._checkRepo)
            self.authToken = authToken
            self.auth = users.Authorization(**auth)
            if self.auth.authorized:
                self._checkRepo = False

            r = method(*args)
        except users.UserAlreadyExists, e:
            return (True, ("UserAlreadyExists", str(e)))
        except database.DuplicateItem, e:
            return (True, ("DuplicateItem", e.item))
        except database.ItemNotFound, e:
            return (True, ("ItemNotFound", e.item))
#        except Exception, error:
#            exc_name = sys.exc_info()[0].__name__
#            return (True, (exc_name, error, ""))
        else:
            return (False, r)

    def _getAuthRepo(self, project):
        authUrl = "http://%s:%s@%s/conary/" % (self.cfg.authUser, self.cfg.authPass,
                                               project.getHostname())
        authLabel = project.getLabel()

        authRepo = {authLabel: authUrl}
        repo = netclient.NetworkRepositoryClient(authRepo)
        return repo

    # project methods
    @requiresAuth
    def newProject(self, projectName, hostname, desc):
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in reservedHosts:
            raise projects.InvalidHostname
        hostname += "." + self.cfg.domainName

        # XXX this set of operations should be atomic if possible
        projectId = self.projects.new(name = projectName,
                                      creatorId = self.auth.userId,
                                      desc = desc,
                                      hostname = hostname,
                                      defaultBranch = "rpl:devel",
                                      timeModified = time.time(),
                                      timeCreated = time.time())
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)
        
        project = projects.Project(self, projectId)
        project.addLabel(hostname + "@rpl:devel",
            "http://%s/conary/" % hostname,
            self.authToken[0], self.authToken[1])

        self.projects.createRepos(self.cfg.reposPath, hostname,
                                  self.authToken[0], self.authToken[1])

        return projectId

    def getProject(self, id):
        return self.projects.get(id)

    def getProjectIdByHostname(self, hostname):
        return self.projects.getProjectIdByHostname(hostname)

    def getProjectIdsByMember(self, userId):
        return self.projects.getProjectIdsByMember(userId)

    def getMembersByProjectId(self, id):
        return self.projectUsers.getMembersByProjectId(id)

    @requiresAuth
    def addMember(self, projectId, userId, username, level):
        assert(level in userlevels.LEVELS)
        project = projects.Project(self, projectId)

        cu = self.db.cursor()
        if username and not userId:
            cu.execute("SELECT userId FROM Users WHERE username=?",
                       username)
            try:
                userId = cu.next()[0]
            except StopIteration, e:
                print >>sys.stderr, str(e), "SELECT userId FROM Users WHERE username=?", username
                sys.stderr.flush()
                raise database.ItemNotFound("user")

        acu = self.authDb.cursor()
        password = ''
        salt = ''
        query = "SELECT salt, password FROM Users WHERE user=?"
        acu.execute(query, username)
        try:
            salt, password = acu.next()
        except StopIteration, e:
            print >>sys.stderr, str(e), query, username
            sys.stderr.flush()
            raise database.ItemNotFound("user")
        except DatabaseError, e:
            print >>sys.stderr, str(e), query, username
            sys.stderr.flush()

        self.projectUsers.new(projectId, userId, level)
        repos = self._getAuthRepo(project)
        repos.addUserByMD5(project.getLabel(), username, salt, password)
        repos.addAcl(project.getLabel(), username, None, None, True, False, level == userlevels.OWNER)

        return True

    @requiresAuth
    def delMember(self, projectId, userId):
        #XXX Make this atomic
        project = projects.Project(self, projectId)
        self.projectUsers.delete(projectId, userId)
        repos = self._getAuthRepo(project)
        repos.deleteUserByName(project.getLabel(), self.getUser(userId)['username'])

    @requiresAuth
    def setProjectDesc(self, projectId, desc):
        return self.projects.update(projectId, desc = desc)

    # user methods
    def getUser(self, id):
        return self.users.get(id)

    def getUserLevel(self, userId, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT level FROM ProjectUsers WHERE userId=? and projectId=?",
                   userId, projectId)
        try:
            l = cu.next()[0]
            return l
        except StopIteration:
            raise database.ItemNotFound("membership")

    def setUserLevel(self, userId, projectId, level):
        cu = self.db.cursor()
        cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and 
            projectId=?""", level, userId, projectId)

        self.db.commit()

    def getProjectsByUser(self, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT hostname, name, level FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=?
                      ORDER BY level, name""", userId)

        rows = []
        for r in cu.fetchall():
            rows.append([r[0], r[1], r[2]])
        return rows

    def registerNewUser(self, username, password, fullName, email, active):
        return self.users.registerNewUser(username, password, fullName, email, active)

    def checkAuth(self):
        return self.auth.getDict()

    @requiresAuth
    def setUserEmail(self, userId, email):
        return self.users.update(userId, email = email)

    @requiresAuth
    def setUserDisplayEmail(self, userId, displayEmail):
        return self.users.update(userId, displayEmail = displayEmail)

    @requiresAuth
    def setUserBlurb(self, userId, blurb):
        return self.users.update(userId, blurb = blurb)

    @requiresAuth
    def setUserFullName(self, userId, fullName):
        return self.users.update(userId, fullName = fullName)

    def confirmUser(self, confirmation):
        userId = self.users.confirm(confirmation)
        return userId

    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

    @requiresAuth
    def setPassword(self, userId, newPassword):
        username = self.users.get(userId)['username']

        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)
        authLabel = self.cfg.authRepoMap.keys()[0]
        authRepo.changePassword(authLabel, username, newPassword)

        for projectId in self.getProjectIdsByMember(userId):
            project = projects.Project(self, projectId)

            authRepo = self._getAuthRepo(project)
            authRepo.changePassword(project.getLabel(), username, newPassword)

        return True

    def searchUsers(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.users.search(terms, limit, offset)

    def searchProjects(self, terms, modified, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param modified: Code for the lastModified filter
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.projects.search(terms, modified, limit, offset)

    def getNews(self):
        return self.newsCache.getNews()

    #
    # LABEL STUFF
    #
    @requiresAuth
    def getLabelsForProject(self, projectId):
        return self.labels.getLabelsForProject(projectId)

    @requiresAuth
    def addLabel(self, projectId, label, url, username, password):
        return self.labels.addLabel(projectId, label, url, username, password)

    @requiresAuth
    def getLabel(self, labelId):
        return self.labels.getLabel(labelId)

    @requiresAuth
    def editLabel(self, labelId, label, url, username, password):
        return self.labels.editLabel(labelId, label, url, username, password)

    @requiresAuth
    def removeLabel(self, projectId, labelId):
        return self.labels.removeLabel(projectId, labelId)

    #
    # RELEASE STUFF
    #
    def getReleasesForProject(self, projectId, showUnpublished = False):
        return [releases.Release(self, x) for x in self.releases.iterReleasesForProject(projectId, showUnpublished)]

    def getRelease(self, releaseId):
        return self.releases.get(releaseId)

    @requiresAuth
    def newRelease(self, projectId, releaseName, published):
        return self.releases.new(projectId = projectId,
                                 name = releaseName,
                                 published = published)

    def getReleaseTrove(self, releaseId):
        return self.releases.getTrove(releaseId)

    @requiresAuth
    def setReleaseTrove(self, releaseId, troveName, troveVersion, troveFlavor):
        return self.releases.setTrove(releaseId, troveName,
                                                 troveVersion,
                                                 troveFlavor)

    @requiresAuth
    def setReleaseDesc(self, releaseId, desc):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET desc=? WHERE releaseId=?",
                   desc, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    def setReleasePublished(self, releaseId, published):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET published=? WHERE releaseId=?",
            published, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    def setImageType(self, releaseId, imageType):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET imageType=? WHERE releaseId=?",
                   imageType, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    def startImageJob(self, releaseId):
        cu = self.db.cursor()

        cu.execute("SELECT jobId, status FROM Jobs WHERE releaseId=?",
                   releaseId)
        r = cu.fetchall()
        if len(r) == 0:
            cu.execute("INSERT INTO Jobs VALUES (NULL, ?, ?, ?, ?, ?, 0)",
                       releaseId, self.auth.userId, jobstatus.WAITING,
                       jobstatus.statusNames[jobstatus.WAITING],
                       time.time())
            retval = cu.lastrowid
        else:
            jobId, status = r[0]
            if status in (jobstatus.WAITING, jobstatus.RUNNING):
                raise jobs.DuplicateJob
            else:
                cu.execute("""UPDATE Jobs SET status=?, statusMessage='Waiting',
                                              timeStarted=?, timeFinished=0
                              WHERE jobId=?""", jobstatus.WAITING, time.time(),
                                                jobId)
                retval = jobId

        self.db.commit()
        return retval

    @requiresAuth
    def getJob(self, jobId):
        cu = self.db.cursor()

        cu.execute("SELECT userId, releaseId, status,"
                   "  statusMessage, timeStarted, "
                   "  timeFinished FROM Jobs "
                   " WHERE jobId=?", jobId)

        p = cu.fetchone()
        if not p:
            raise jobs.JobMissing

        dataKeys = ['userId', 'releaseId', 'status',
                    'statusMessage', 'timeStarted', 'timeFinished']
        data = {}
        for i, key in enumerate(dataKeys):
            data[key] = p[i]
        return data

    @requiresAuth
    def getJobIds(self, releaseId):
        cu = self.db.cursor()

        stmt = """SELECT jobId FROM JOBS"""
        if releaseId != -1:
            stmt += " WHERE releaseId=?"
            cu.execute(stmt, releaseId)
        else:
            cu.execute(stmt)

        p = cu.fetchall()
        rows = []
        for row in p:
            rows.append(row[0])
        return rows
    
    @requiresAuth
    def getGroupTroves(self, projectId):
        project = projects.Project(self, projectId)

        labelIdMap = project.getLabelIdMap()
        cfg = project.getConaryConfig()
        netclient = repository.netclient.NetworkRepositoryClient(cfg.repositoryMap)
        
        troveDict = {}
        for label in labelIdMap.keys():
            troves = allTroveNames.getTroveNames(versions.Label(label), netclient)
            troves = [x for x in troves if (x.startswith("group-") or\
                                            x.startswith("fileset-")) and\
                                            ":" not in x]
            troveDict[label] = troves

        return troveDict

    def __init__(self, cfg):
        self.cfg = cfg
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        self.authDb = sqlite3.connect(cfg.authDbPath, timeout = 30000)

        self.projects = projects.ProjectsTable(self.db, self.cfg)
        self.labels = projects.LabelsTable(self.db)
        self.jobs = jobs.JobsTable(self.db)
        self.users = users.UsersTable(self.db, self.cfg)
        self.projectUsers = users.ProjectUsersTable(self.db)
        self.releases = releases.ReleasesTable(self.db)
        self.newsCache = news.NewsCacheTable(self.db, self.cfg)
        self.newsCache.refresh()

#
# Copyright (c) 2005 rPath, Inc.
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
import pkgindex
import projects
import releases
import versions
import users
import userlevels
from cache import TroveNamesCache
from mint_error import MintError
from mint_error import PermissionDenied

import repository.netrepos.netauth
from repository import netclient

validHost = re.compile('^[a-zA-Z][a-zA-Z0-9\-]*$')
reservedHosts = ['admin', 'mail', 'mint', 'www', 'web', 'rpath', 'wiki', 'conary']

allTroveNames = TroveNamesCache()

def requiresAdmin(func):
    def wrapper(self, *args):
        print >>sys.stderr, self.authToken, self.auth.groups, self.auth.admin
        sys.stderr.flush()
        if self.authToken == [self.cfg.authUser, self.cfg.authPass] or self.auth.admin:
            return func(self, *args)
        else:
            raise PermissionDenied
    return wrapper

def requiresAuth(func):
    def wrapper(self, *args):
        if not self.auth.authorized:
            raise PermissionDenied
        else:
            return func(self, *args)
    return wrapper

def private(func):
    """Mark a method as callable only if self._allowPrivate is set
    to mask out functions not callable via XMLRPC over the web."""
    def wrapper(self, *args):
        if self._allowPrivate:
            return func(self, *args)
        else:
            raise PermissionDenied
    return wrapper

class MintServer(object):
    _checkRepo = True 
    _cachedGroups = []

    def callWrapper(self, methodName, authToken, args):
        if methodName.startswith('_'):
            raise AttributeError
        try:
            method = self.__getattribute__(methodName)
        except AttributeError:
            return (True, ("MethodNotSupported", methodName, ""))
        try:
            # check authorization
            auth = self.users.checkAuth(authToken, checkRepo = self._checkRepo, cachedGroups = self._cachedGroups)
            self.authToken = authToken
            self.auth = users.Authorization(**auth)
            self._cachedGroups = self.auth.groups
            
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
                                               project.getFQDN())
        authLabel = project.getLabel()

        authRepo = {authLabel: authUrl}
        repo = netclient.NetworkRepositoryClient(authRepo)
        return repo

    # project methods
    @requiresAuth
    @private
    def newProject(self, projectName, hostname, domainname, projecturl, desc):
        if validHost.match(hostname) == None:
            raise projects.InvalidHostname
        if hostname in reservedHosts:
            raise projects.InvalidHostname
        fqdn = ".".join((hostname, domainname))

        # XXX this set of operations should be atomic if possible
        projectId = self.projects.new(name = projectName,
                                      creatorId = self.auth.userId,
                                      desc = desc,
                                      hostname = hostname,
                                      domainname = domainname,
                                      projecturl = projecturl,
                                      timeModified = time.time(),
                                      timeCreated = time.time())
        self.projectUsers.new(userId = self.auth.userId,
                              projectId = projectId,
                              level = userlevels.OWNER)
        
        project = projects.Project(self, projectId)
        project.addLabel(fqdn + "@%s"%self.cfg.defaultBranch,
            "http://%s/conary/" % fqdn,
            self.cfg.authUser, self.cfg.authPass)

        self.projects.createRepos(self.cfg.reposPath, hostname, domainname,
                                  self.authToken[0], self.authToken[1])

        return projectId
    
    @private
    def getProject(self, id):
        return self.projects.get(id)

    @private
    def getProjectIdByFQDN(self, fqdn):
        return self.projects.getProjectIdByFQDN(fqdn)

    @private
    def getProjectIdsByMember(self, userId):
        return self.projects.getProjectIdsByMember(userId)

    @private
    def getMembersByProjectId(self, id):
        return self.projectUsers.getMembersByProjectId(id)

    @requiresAdmin
    @private
    def getOwnersByProjectName(self, name):
        return self.projectUsers.getOwnersByProjectName(name)

    @requiresAuth
    @private
    def addMember(self, projectId, userId, username, level):
        assert(level in userlevels.LEVELS)
        project = projects.Project(self, projectId)

        cu = self.db.cursor()
        if username and not userId:
            cu.execute("SELECT userId FROM Users WHERE username=?", username)
            try:
                userId = cu.next()[0]
            except StopIteration, e:
                raise database.ItemNotFound("user")
        elif userId and not username:
            username = self.users.getUsername(userId)

        acu = self.authDb.cursor()
        password = ''
        salt = ''
        query = "SELECT salt, password FROM Users WHERE user=?"
        acu.execute(query, username)
        try:
            salt, password = acu.next()
        except StopIteration, e:
            raise database.ItemNotFound("user")
        except DatabaseError, e:
            raise

        self.projectUsers.new(projectId, userId, level)
        repos = self._getAuthRepo(project)
        repos.addUserByMD5(project.getLabel(), username, salt, password)
        repos.addAcl(project.getLabel(), username, None, None, True, False, level == userlevels.OWNER)

        self._notifyUser('Added', self.getUser(userId), projects.Project(self,projectId)) 

        return True

    @requiresAuth
    @private
    def delMember(self, projectId, userId, notify=True):
        #XXX Make this atomic
        project = projects.Project(self, projectId)
        self.projectUsers.delete(projectId, userId)
        repos = self._getAuthRepo(project)
        user = self.getUser(userId)
        repos.deleteUserByName(project.getLabel(), user['username'])
        if notify:
            self._notifyUser('Removed', user, project)

    def _notifyUser(self, action, user, project, userlevel=None):
        actionText = {'Removed': "You have been removed from the project",
            'Added': "You have been added to the project",
            'Changed': "Your current access level is %s" % (userlevel and userlevels.names[userlevel] or 'Unknown')
        }
        greeting = "%s," % (user['fullName'] and user['fullName'] or user['username'])
        message = "An owner of %s has modified your account status: "%project.getName()
        message += actionText[action]
        message += '.'
        closing = 'Please contact the project owner(s) with any questions.'

        users.sendMail(self.cfg.adminMail, self.cfg.productName,
                    user['email'],
                    "%s user modification" % project.getName(),
                    '\n\n'.join((greeting, message, closing)))

    @requiresAuth
    @private
    def editProject(self, projectId, projecturl, desc):
        return self.projects.update(projectId, projecturl=projecturl, desc = desc)

    # user methods
    @private
    def getUser(self, id):
        return self.users.get(id)

    @private
    def getUserLevel(self, userId, projectId):
        cu = self.db.cursor()
        cu.execute("SELECT level FROM ProjectUsers WHERE userId=? and projectId=?",
                   userId, projectId)
        try:
            l = cu.next()[0]
            return l
        except StopIteration:
            raise database.ItemNotFound("membership")

    @requiresAuth
    @private
    def setUserLevel(self, userId, projectId, level):
        cu = self.db.cursor()
        cu.execute("""UPDATE ProjectUsers SET level=? WHERE userId=? and 
            projectId=?""", level, userId, projectId)

        self.db.commit()
        self._notifyUser('Changed', self.getUser(userId), projects.Project(self, projectId), level)

    @private
    def getProjectsByUser(self, userId):
        cu = self.db.cursor()
        cu.execute("""SELECT hostname||'.'||domainname, name, level
                      FROM Projects, ProjectUsers
                      WHERE Projects.projectId=ProjectUsers.projectId AND
                            ProjectUsers.userId=?
                      ORDER BY level, name""", userId)

        rows = []
        for r in cu.fetchall():
            rows.append([r[0], r[1], r[2]])
        return rows

    @private
    def registerNewUser(self, username, password, fullName, email, displayEmail, blurb, active):
        return self.users.registerNewUser(username, password, fullName, email, displayEmail, blurb, active)

    @private
    def checkAuth(self):
        return self.auth.getDict()
        
    @requiresAuth
    @private
    def updateAccessedTime(self, userId):
        return self.users.update(userId, timeAccessed = time.time())

    @requiresAuth
    @private
    def setUserEmail(self, userId, email):
        return self.users.update(userId, email = email)

    @requiresAuth
    @private
    def validateNewEmail(self, userId, email):
        return self.users.validateNewEmail(userId, email)

    @requiresAuth
    @private
    def setUserDisplayEmail(self, userId, displayEmail):
        return self.users.update(userId, displayEmail = displayEmail)

    @requiresAuth
    @private
    def setUserBlurb(self, userId, blurb):
        return self.users.update(userId, blurb = blurb)

    @requiresAuth
    @private
    def setUserFullName(self, userId, fullName):
        return self.users.update(userId, fullName = fullName)

    @requiresAuth
    @private
    def cancelUserAccount(self, userId):
        """ Checks to see if the the user to be deleted is leaving in a lurch developers of projects that would be left ownerless.  Then deletes the user.
        """
        cu = self.db.cursor()
        username = self.users.getUsername(userId)

        # Find all projects of which userId is an owner, has no other owners, and/or
        # has developers.
        cu.execute("""SELECT MAX(flagged)
                        FROM (SELECT A.projectId,
                               COUNT(B.userId)*not(COUNT(C.userId)) AS flagged
                                 FROM ProjectUsers AS A
                                   LEFT JOIN ProjectUsers AS B ON A.projectId=B.projectId AND B.level=1
                                   LEFT JOIN ProjectUsers AS C ON C.projectId=A.projectId AND
                                                                  C.level = 0 AND
                                                                  C.userId <> A.userId AND
                                                                  A.level = 0
                                       WHERE A.userId=? GROUP BY A.projectId)
                   """, userId)

        try:
            r = cu.next()
            if r[0]:
                raise users.LastOwner
        except database.StopIteration:
            pass

        return self.removeUserAccount(userId)

    @requiresAuth
    @private
    def removeUserAccount(self, userId):
        """Removes the user account from the authrepo and mint databases.
        Also removes the user from each project listed in projects.
        """
        if not self.auth.admin and userId != self.auth.userId:
            raise PermissionDenied
        repoLabel = self.cfg.authRepoMap.keys()[0]
        username = self.users.getUsername(userId)
        cu = self.db.cursor()
        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)

        #Handle projects
        projectlist = self.getProjectIdsByMember(userId)
        for (projectId, level) in projectlist:
            self.delMember(projectId, userId, False)

        authRepo.deleteUserByName(repoLabel, username)

        cu.execute("UPDATE Projects SET creatorId=NULL WHERE creatorId=?", userId)
        cu.execute("UPDATE Jobs SET userId=NULL WHERE userId=?", userId)
        cu.execute("DELETE FROM ProjectUsers WHERE userId=?", userId)
        cu.execute("DELETE FROM Confirmations WHERE userId=?", userId)
        cu.execute("DELETE FROM Users WHERE userId=?", userId)

        self.db.commit()

    @private
    def confirmUser(self, confirmation):
        userId = self.users.confirm(confirmation)
        return userId

    @private
    def getUserIdByName(self, username):
        return self.users.getIdByColumn("username", username)

    @private
    def setPassword(self, userId, newPassword):
        username = self.users.get(userId)['username']

        for projectId, level in self.getProjectIdsByMember(userId):
            project = projects.Project(self, projectId)

            authRepo = self._getAuthRepo(project)
            authRepo.changePassword(project.getLabel(), username, newPassword)

        authRepo = netclient.NetworkRepositoryClient(self.cfg.authRepoMap)
        authLabel = self.cfg.authRepoMap.keys()[0]
        authRepo.changePassword(authLabel, username, newPassword)

        return True

    @requiresAdmin
    @private
    def searchUsers(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.users.search(terms, limit, offset)

    @private
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

    @private
    def searchPackages(self, terms, limit, offset):
        """
        Collect the results as requested by the search terms
        @param terms: Search terms
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        @return:       dictionary of Items requested
        """
        return self.pkgIndex.search(terms, limit, offset)

    @private
    def getProjectsList(self):
        """
        Collect a list of all projects suitable for creating a select box
        """
        return self.projects.getProjectsList()

    @private
    def getProjects(self, sortOrder, limit, offset):
        """
        Collect a list of projects
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        return self.projects.getProjects(sortOrder, limit, offset), self.projects.getNumProjects()

    @requiresAdmin
    @private
    def getUsersList(self):
        return self.users.getUsersList()

    @requiresAdmin
    @private
    def getUsers(self, sortOrder, limit, offset):
        """
        Collect a list of projects
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        return self.users.getUsers(sortOrder, limit, offset), self.users.getNumUsers()

    def getNews(self):
        return self.newsCache.getNews()

    def getNewsLink(self):
        return self.newsCache.getNewsLink()

    #
    # LABEL STUFF
    #
    @private
    def getDefaultProjectLabel(self, projectId):
        return self.labels.getDefaultProjectLabel(projectId)

    @requiresAuth
    @private
    def getLabelsForProject(self, projectId):
        """Returns a mapping of labels to labelIds and a repository map dictionary for the current user"""
        return self.labels.getLabelsForProject(projectId)

    @requiresAuth
    @private
    def addLabel(self, projectId, label, url, username, password):
        return self.labels.addLabel(projectId, label, url, username, password)

    @requiresAuth
    @private
    def getLabel(self, labelId):
        return self.labels.getLabel(labelId)

    @requiresAuth
    @private
    def editLabel(self, labelId, label, url, username, password):
        return self.labels.editLabel(labelId, label, url, username, password)

    @requiresAuth
    @private
    def removeLabel(self, projectId, labelId):
        return self.labels.removeLabel(projectId, labelId)

    #
    # RELEASE STUFF
    #
    @private
    def getReleasesForProject(self, projectId, showUnpublished = False):
        return [releases.Release(self, x) for x in self.releases.iterReleasesForProject(projectId, showUnpublished)]

    @private
    def getRelease(self, releaseId):
        return self.releases.get(releaseId)

    @requiresAuth
    @private
    def newRelease(self, projectId, releaseName, published):
        return self.releases.new(projectId = projectId,
                                 name = releaseName,
                                 published = published)

    @private
    def getReleaseTrove(self, releaseId):
        return self.releases.getTrove(releaseId)

    @requiresAuth
    @private
    def setReleaseTrove(self, releaseId, troveName, troveVersion, troveFlavor):
        return self.releases.setTrove(releaseId, troveName,
                                                 troveVersion,
                                                 troveFlavor)

    @requiresAuth
    @private
    def setReleaseDesc(self, releaseId, desc):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET desc=? WHERE releaseId=?",
                   desc, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    @private
    def setReleasePublished(self, releaseId, published):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET published=? WHERE releaseId=?",
            published, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    @private
    def setImageType(self, releaseId, imageType):
        cu = self.db.cursor()
        cu.execute("UPDATE Releases SET imageType=? WHERE releaseId=?",
                   imageType, releaseId)
        self.db.commit()
        return True

    @requiresAuth
    @private
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
    @private
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
    @private
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
    @private
    def setJobStatus(self, jobId, newStatus, statusMessage):
        cu = self.db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage=? WHERE jobId=?",
                   newStatus, statusMessage, jobId)
        if newStatus == jobstatus.FINISHED:
            cu.execute("UPDATE Jobs SET timeFinished=? WHERE jobId=?",
                       time.time(), jobId)
        self.db.commit()
        return True

    @requiresAuth
    @private
    def setImageFilenames(self, releaseId, filenames):
        cu = self.db.cursor()
        cu.execute("DELETE FROM ImageFiles WHERE releaseId=?", releaseId)
        for idx, file in enumerate(sorted(filenames)):
            cu.execute("INSERT INTO ImageFiles VALUES (NULL, ?, ?, ?)",
                       releaseId, idx, file)
        self.db.commit()
        return True

    @private
    def getImageFilenames(self, releaseId):
        cu = self.db.cursor()
        cu.execute("SELECT fileId, filename FROM ImageFiles WHERE releaseId=? ORDER BY idx", releaseId)

        results = cu.fetchall()
        if len(results) < 1:
            return []
        else:
            return [(x[0], x[1]) for x in results]
   
    @private
    def getFilename(self, fileId):
        cu = self.db.cursor()
        cu.execute("SELECT filename FROM ImageFiles WHERE fileId=?", fileId)

        results = cu.fetchone()
        if results:
            return results[0]
        else:
            raise jobs.FileMissing

    @requiresAuth
    def getGroupTroves(self, projectId):
        # enable internal methods so that public methods can make 
        # private calls; this is safe because only one instance
        # of MintServer is instantiated per call.
        self._allowPrivate = True

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

    @requiresAuth
    def getReleaseStatus(self, releaseId):
        self._allowPrivate = True

        release = releases.Release(self, releaseId)
        job = release.getJob()

        if not job:
            return {'status': -1, 'message': 'No job.'}
        else:
            return {'status':  job.getStatus(),
                    'message': job.getStatusMessage()}

    def __init__(self, cfg, allowPrivate = False):
        self.cfg = cfg
     
        # all methods are private (not callable via XMLRPC)
        # except the ones specifically decorated with @public.
        self._allowPrivate = allowPrivate
        
        self.db = sqlite3.connect(cfg.dbPath, timeout = 30000)
        self.authDb = sqlite3.connect(cfg.authDbPath, timeout = 30000)

        self.projects = projects.ProjectsTable(self.db, self.cfg)
        self.labels = projects.LabelsTable(self.db)
        self.jobs = jobs.JobsTable(self.db)
        self.users = users.UsersTable(self.db, self.cfg)
        self.projectUsers = users.ProjectUsersTable(self.db)
        self.releases = releases.ReleasesTable(self.db)
        self.pkgIndex = pkgindex.PackageIndexTable(self.db)
        self.newsCache = news.NewsCacheTable(self.db, self.cfg)
        self.newsCache.refresh()

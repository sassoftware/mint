#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import os
import sys
import urlparse
import time

import sqlite3
import versions
from lib import util
from repository.netrepos.netserver import NetworkRepositoryServer
from conarycfg import ConaryConfiguration
import mailinglists

from mint_error import MintError
import database
import userlevels
import searcher

import projectlisting

class InvalidHostname(MintError):
    def __str__(self):
        return "invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."

class DuplicateHostname(MintError):
    def __str__(self):
        return "A project using this hostname already exists"

class DuplicateName(MintError):
    def __str__(self):
        return "A project using this project title already exists"

class Project(database.TableObject):
    __slots__ = ('creatorId', 'name',
                 'desc', 'hostname', 'domainname', 'projecturl', 
                 'hidden', 'external', 'disabled',
                 'timeCreated', 'timeModified')

    def getItem(self, id):
        return self.server.getProject(id)

    def getCreatorId(self):
        return self.creatorId

    def getName(self):
        return self.name

    def getDomainname(self):
        return self.domainname

    def getProjectUrl(self):
        return self.projecturl

    def getHostname(self):
        return self.hostname

    def getFQDN(self):
        return '.'.join((self.hostname, self.domainname))

    def getLabel(self):
        return self.server.getDefaultProjectLabel(self.id)

    def getDesc(self):
        return self.desc

    def getTimeCreated(self):
        return self.timeCreated

    def getTimeModified(self):
        return self.timeModified

    def getMembers(self):
        return self.server.getMembersByProjectId(self.id)

    def getReleases(self, showUnpublished = False):
        return self.server.getReleasesForProject(self.id, showUnpublished)

    def getCommits(self):
        return self.server.getCommitsForProject(self.id)

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except database.ItemNotFound:
            return userlevels.NONMEMBER

    def updateUserLevel(self, userId, level):
        return self.server.setUserLevel(userId, self.id, level)

    def addMemberById(self, userId, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, userId, None, level)

    def addMemberByName(self, username, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, None, username, level)

    def listJoinRequests(self):
        return self.server.listJoinRequests(self.id)

    def delMemberById(self, userId):
        return self.server.delMember(self.id, userId)

    def editProject(self, projecturl, desc):
        return self.server.editProject(self.id, projecturl, desc)

    def updateUser(self, userId, **kwargs):
        return self.users.update(userId, **kwargs)

    def getRepoMap(self):
        labelPath, repoMap = self.server.getLabelsForProject(self.id, None, None, None)
        return [x[0] + " " + x[1] for x in repoMap.items()]

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        labelPath, repoMap = self.server.getLabelsForProject(self.id, None, None, None)
        return labelPath

    def getConaryConfig(self, newUser = None, newPass = None, useSSL = None):
        labelPath, repoMap = self.server.getLabelsForProject(self.id, newUser, newPass, useSSL)

        cfg = ConaryConfiguration(readConfigFiles=False)
        cfg.initializeFlavors()

        installLabelPath = " ".join(x for x in labelPath.keys())
        cfg.setValue("installLabelPath", installLabelPath)

        for m in [x[0] + " " + x[1] for x in repoMap.items()]:
            cfg.setValue("repositoryMap", m)
        return cfg

    def addLabel(self, label, url, username="", password=""):
        return self.server.addLabel(self.id, label, url, username, password)

    def getLabelIds(self):
        labelPath, repoMap = self.server.getLabelsForProject(self.id, None, None, None)
        return labelPath.values()

    def getLabelById(self, labelId):
        labelPath, repoMap = self.server.getLabelsForProject(self.id, None, None, None)
        # turn labelPath inside-out
        revMap = dict(zip(labelPath.values(), labelPath.keys()))

        return revMap[int(labelId)]

    def editLabel(self, labelId, label, url, username, password):
        return self.server.editLabel(labelId, label, url, username, password)

    def removeLabel(self, labelId):
        return self.server.removeLabel(self.id, labelId)

    def addUserKey(self, username, keydata):
        return self.server.addUserKey(self.id, username, keydata)

    def orphan(self, mlbaseurl, mlpasswd):
        #Take care of mailing lists
        mlists = mailinglists.MailingListClient(mlbaseurl + 'xmlrpc/')
        return mlists.orphan_lists(mlpasswd, self.getName())

    def adopt(self, auth, mlbaseurl, mlpasswd):
        self.addMemberByName(auth.username, userlevels.OWNER)
        # Take care of mailing lists
        mlists = mailinglists.MailingListClient(mlbaseurl + 'xmlrpc/')
        mlists.adopt_lists(auth, mlpasswd, self.getName())


class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    createSQL = """CREATE TABLE Projects (
                    projectId       INTEGER PRIMARY KEY,
                    creatorId       INT,
                    name            STR UNIQUE,
                    hostname        STR UNIQUE,
                    domainname      STR DEFAULT '' NOT NULL,
                    projecturl      STR DEFAULT '' NOT NULL,
                    desc            STR NOT NULL DEFAULT '',
                    disabled        INT DEFAULT 0,
                    hidden          INT DEFAULT 0,
                    external        INT DEFAULT 0,
                    timeCreated     INT,
                    timeModified    INT DEFAULT 0
                )"""
    fields = ['creatorId', 'name', 'hostname', 'domainname', 'projecturl', 
              'desc', 'disabled', 'hidden', 'external', 'timeCreated', 'timeModified']
    indexes = { "ProjectsHostnameIdx": "CREATE INDEX ProjectsHostnameIdx ON Projects(hostname)",
                "ProjectsDisabledIdx": "CREATE INDEX ProjectsDisabledIdx ON Projects(disabled)",
                "ProjectsHiddenIdx": "CREATE INDEX ProjectsHiddenIdx ON Projects(hidden)"
              }

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def versionCheck(self):
        dbversion = self.getDBVersion()
        if dbversion != self.schemaVersion:
            if dbversion == 0:
                sql = """ALTER TABLE Projects ADD COLUMN hidden INT DEFAULT 0"""
                cu = self.db.cursor()
                try:
                    cu.execute(sql)
                except:
                    return False
            if dbversion == 2:
                cu = self.db.cursor()
                try:
                    cu.execute("ALTER TABLE Projects ADD COLUMN external INT DEFAULT 0")
                    cu.execute("UPDATE Projects SET external=0")
                except:
                    return False
                    
        return True

    def new(self, **kwargs):
        try:
            id = database.KeyedTable.new(self, **kwargs)
        except database.DuplicateItem, e:
            cu = self.db.cursor()
            cu.execute("SELECT projectId FROM Projects WHERE hostname=?", kwargs['hostname'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateHostname()
            cu.execute("SELECT projectId FROM Projects WHERE name=?", kwargs['name'])
            results = cu.fetchall()
            if len(results) > 0:
                raise DuplicateName()
        return id

    def getProjectsList(self):
        cu = self.db.cursor()

        sql = """
            SELECT projectId, disabled, hidden, hostname || ' - ' || name 
            FROM Projects
            ORDER BY hostname
        """
        cu.execute(sql)

        results = cu.fetchall()
        return results

    def getProjectIdByFQDN(self, fqdn):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname || '.' || domainname=? AND disabled=0", fqdn)

        try:
            r = cu.next()
        except StopIteration:
            raise database.ItemNotFound
        return r[0]

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname=? AND disabled=0", hostname)

        try:
            r = cu.next()
        except StopIteration:
            raise database.ItemNotFound
        return r[0]

    def getProjectIdsByMember(self, userId):
        cu = self.db.cursor()
        cu.execute("SELECT projectId, level FROM ProjectUsers WHERE userId=?", userId)

        ids = []
        for r in cu.fetchall():
            ids.append((r[0], r[1]))
        return ids

    def getNumProjects(self):
        cu = self.db.cursor()
        cu.execute("SELECT count(name) FROM Projects WHERE disabled=0 AND hidden=0")

        return cu.next()[0]

    def getProjects(self, sortOrder, limit, offset):
        """ Return a list of projects with no filtering whatsoever
        @param sortOrder: Order the projects by this criteria
        @param limit:  Number of items to return
        @param offset: Count at which to begin listing
        """
        cu = self.db.cursor()

        SQL = projectlisting.sqlbase % (projectlisting.ordersql[sortOrder],
            limit, offset)
        cu.execute(SQL)

        ids = []
        for x in cu:
            ids.append(list(x))
            if len(ids[-1][projectlisting.descindex]) > projectlisting.desctrunclength:
                ids[-1][projectlisting.descindex] = ids[-1][projectlisting.descindex][:projectlisting.desctrunclength] + "..."

        return ids

    def search(self, terms, modified, limit, offset):
        """
        Returns a list of projects matching L{terms} of length L{limit}
        starting with item L{offset}.
        @param terms: Search terms
        @param modified: Code for the period within which the project must have been modified to include in the search results.
        @param offset: Count at which to begin listing
        @param limit:  Number of items to return
        @return:       a dictionary of the requested items.
                       each entry will contain four bits of data:
                        The hostname for use with linking,
                        The project name,
                        The project's description
                        The date last modified.
        """
        columns = ['hostname', 'name', 'desc', 'timeModified']
        searchcols = ['name', 'desc']
        ids, count = database.KeyedTable.search(self, columns, 'Projects', 
            searcher.Searcher.where(terms, searchcols, 'AND disabled=0 AND hidden=0'),
            'NAME', searcher.Searcher.lastModified('timeModified', modified),
            limit, offset)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][2] = searcher.Searcher.truncate(x[2], terms)

        return ids, count

    def createRepos(self, reposPath, contentsPath, hostname, domainname, username, password):
        dbPath = os.path.join(reposPath, hostname + "." + domainname)
        contentsPath = os.path.join(contentsPath, hostname + "." + domainname)
        tmpPath = os.path.join(dbPath, 'tmp')
        util.mkdirChain(tmpPath)

        repos = EmptyNetworkRepositoryServer(dbPath, contentsPath, None, None, None, {})
        repos.auth.addUser(username, password)
        repos.auth.addAcl(username, None, None, True, False, True)

        repos.auth.addUser("anonymous", "anonymous")
        repos.auth.addAcl("anonymous", None, None, False, False, False)

        # add the mint auth user so we can add additional permissions
        # to this repository
        repos.auth.addUser(self.cfg.authUser, self.cfg.authPass)
        repos.auth.addAcl(self.cfg.authUser, None, None, True, False, True)

    def hide(self, projectId):
        # Anonymous user is added/removed in mint_server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=1, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

    def unhide(self, projectId):
        # Anonymous user is added/removed in mint_server
        cu = self.db.cursor()

        cu.execute("UPDATE Projects SET hidden=0, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

    def disable(self, projectId, reposPath):
        cu = self.db.cursor()

        # now move the repository out of the way
        project = self.get(projectId)
        path = os.path.join(reposPath, project['hostname'] + '.' + project['domainname'])
        os.rename(path, path+'.disabled')

        cu.execute("UPDATE Projects SET disabled=1, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

    def enable(self, projectId, reposPath):
        cu = self.db.cursor()

        # now move the repository back
        project = self.get(projectId)
        path = os.path.join(reposPath, project['hostname'] + '.' + project['domainname'])
        os.rename(path+'.disabled', path)

        cu.execute("UPDATE Projects SET disabled=0, timeModified=? WHERE projectId=?", time.time(), projectId)
        self.db.commit()

class LabelsTable(database.KeyedTable):
    name = 'Labels'
    key = 'labelId'

    createSQL = """CREATE TABLE Labels (
                    labelId         INTEGER PRIMARY KEY,
                    projectId       INT,
                    label           STR,
                    url             STR,
                    username        STR,
                    password        STR
                )"""

    fields = ['labelId', 'projectId', 'label', 'url', 'username', 'password']

    def getDefaultProjectLabel(self, projectId):
        cu = self.db.cursor()

        cu.execute ("""SELECT label 
                      FROM Labels 
                      WHERE projectId=?
                      ORDER BY projectId LIMIT 1""", projectId)

        label = cu.fetchone()
        return label[0]

    def getLabelsForProject(self, projectId, useSSL = None, newUser = None, newPass = None):
        cu = self.db.cursor()

        cu.execute("""SELECT labelId, label, url, username, password
                      FROM Labels
                      WHERE projectId=?""", projectId)

        repoMap = {}
        labelIdMap = {}
        for labelId, label, url, username, password in cu:
            if newUser and newPass:
                username = newUser
                password = newPass

            labelIdMap[label] = labelId
            host = label[:label.find('@')]
            if url:
                if username and password:
                    urlparts = urlparse.urlparse(url)

                    if useSSL == None: # don't override what the db says
                        protocol = urlparts[0]
                    elif useSSL == True:
                        protocol = "https"
                    else:
                        protocol = "http"
                    map = "".join((protocol, "://%s:%s@" % (username, password)) + urlparts[1:])
                else:
                    map = url
            else:
                map = "http://%s/conary/" % (host)

            repoMap[host] = map

        return labelIdMap, repoMap

    def getLabel(self, labelId):
        cu = self.db.cursor()
        cu.execute("SELECT label, url, username, password FROM Labels WHERE labelId=?", labelId)

        p = cu.fetchone()
        if not p:
            raise LabelMissing
        else:
            return p[0], p[1], p[2], p[3]

    def addLabel(self, projectId, label, url=None, username=None, password=None):
        cu = self.db.cursor()

        cu.execute("""SELECT count(labelId) FROM Labels WHERE label=? and projectId=?""",
                   label, projectId)
        c = cu.fetchone()[0]
        if c > 0:
            raise DuplicateLabel

        cu.execute("""INSERT INTO Labels (projectId, label, url, username, password)
                      VALUES (?, ?, ?, ?, ?)""", projectId, label, url, username, password)
        self.db.commit()
        return cu.lastrowid

    def editLabel(self, labelId, label, url, username=None, password=None):
        cu = self.db.cursor()
        cu.execute("""UPDATE Labels SET label=?, url=?, username=?, password=?
                      WHERE labelId=?""", label, url, username, password, labelId)
        self.db.commit()
        return False

    def removeLabel(self, projectId, labelId):
        cu = self.db.cursor()

        cu.execute("""SELECT p.troveVersion, l.label
                      FROM Releases p, Labels l
                      WHERE p.projectId=?
                        AND l.projectId=p.projectId
                        AND l.labelId=?""",
                   projectId, labelId)

        for versionStr, label in cu:
            if versionStr:
                v = versions.ThawVersion(versionStr)
                if v.branch().label().asString() == label:
                    raise LabelInUse

        cu.execute("""DELETE FROM Labels WHERE projectId=? AND labelId=?""", projectId, labelId)
        self.db.commit()
        return False
    
# XXX sort of stolen from conary/server/server.py
class EmptyNetworkRepositoryServer(NetworkRepositoryServer):
    def __init__(self, dbPath, contentsPath, tmpPath, basicUrl, name,
                 repositoryMap, commitAction = None, cacheChangeSets = False,
                 logFile = None):
        if dbPath != contentsPath:
            #Create the links as appropriate.  dbPath will be the ultimate path sent
            # up to NetworkRepositoryServer.
            contentsTarget = os.path.join(dbPath, 'contents')
            contentsSrc = os.path.join(contentsPath, 'contents')
            util.mkdirChain(contentsSrc)
            os.symlink(contentsSrc, contentsTarget)
        NetworkRepositoryServer.__init__(self, dbPath, tmpPath, basicUrl, name, repositoryMap, commitAction, cacheChangeSets, logFile)

    def reset(self, authToken, clientVersion):
        import shutil
        shutil.rmtree(self.repPath + '/contents')
        os.mkdir(self.repPath + '/contents')

        # cheap trick. sqlite3 doesn't mind zero byte files; just replace
        # the file with a zero byte one (to change the inode) and reopen
        open(self.repPath + '/sqldb.new', "w")
        os.rename(self.repPath + '/sqldb.new', self.repPath + '/sqldb')
        self.reopen()

        return 0

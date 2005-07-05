#
# Copyright (c) 2005 rpath, Inc.
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

from mint_error import MintError
import database
import userlevels
import searcher

class InvalidHostname(Exception):
    def __str__(self):
        return "invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."

class Project(database.TableObject):
    __slots__ = ('creatorId', 'name',
                 'desc', 'hostname', 'defaultBranch',
                 'timeCreated', 'timeModified')

    def getItem(self, id):
        return self.server.getProject(id)

    def getCreatorId(self):
        return self.creatorId

    def getName(self):
        return self.name

    def getHostname(self):
        return self.hostname

    def getLabel(self):
        return self.hostname + "@" + self.defaultBranch

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

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(userId, self.id)
        except database.ItemNotFound:
            return -1

    def updateUserLevel(self, userId, level):
        return self.server.setUserLevel(userId, self.id, level)

    def addMemberById(self, userId, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, userId, None, level)

    def addMemberByName(self, username, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, None, username, level)

    def delMemberById(self, userId):
        return self.server.delMember(self.id, userId)

    def setDesc(self, desc):
        return self.server.setProjectDesc(self.id, desc)

    def updateUser(self, userId, **kwargs):
        return self.users.update(userId, **kwargs)

    def getRepoMap(self):
        labelPath, repoMap = self.server.getLabelsForProject(self.id)
        return [x[0] + " " + x[1] for x in repoMap.items()]

    def getLabelIdMap(self):
        """Returns a dictionary mapping of label names to database IDs"""
        labelPath, repoMap = self.server.getLabelsForProject(self.id)
        return labelPath

    def getConaryConfig(self, imageLabel=None, imageRepo=None):
        labelPath, repoMap = self.server.getLabelsForProject(self.id)

        cfg = ConaryConfiguration(readConfigFiles=False)
        cfg.initializeFlavors()

        installLabelPath = " ".join(x for x in labelPath.keys())

        if imageLabel:
            installLabelPath += " " + imageLabel
        cfg.setValue("installLabelPath", installLabelPath)

        for m in [x[0] + " " + x[1] for x in repoMap.items()]:
            cfg.setValue("repositoryMap", m)
        if imageRepo:
            cfg.setValue("repositoryMap", "%s %s" % (imageLabel.split('@')[0],
                                                     imageRepo))
        return cfg

    def addLabel(self, label, url, username="", password=""):
        return self.server.addLabel(self.id, label, url, username, password)

    def getLabelIds(self):
        labelPath, repoMap = self.server.getLabelsForProject(self.id)
        return labelPath.values()

    def getLabel(self, labelId):
        labelPath, repoMap = self.server.getLabelsForProject(self.id)
        # turn labelPath inside-out
        revMap = dict(zip(labelPath.values(), labelPath.keys()))

        return revMap[int(labelId)]

    def editLabel(self, labelId, label, url, username, password):
        return self.server.editLabel(labelId, label, url, username, password)

    def removeLabel(self, labelId):
        return self.server.removeLabel(self.id, labelId)


class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    createSQL = """CREATE TABLE Projects (
                    projectId       INTEGER PRIMARY KEY,
                    creatorId       INT,
                    name            STR UNIQUE,
                    hostname        STR UNIQUE,
                    defaultBranch   STR,
                    desc            STR,
                    timeCreated     INT,
                    timeModified    INT DEFAULT 0,
                );"""
    fields = ['creatorId', 'name', 'hostname', 'defaultBranch',
              'desc', 'timeCreated', 'timeModified']

    def __init__(self, db, cfg):
        database.DatabaseTable.__init__(self, db)
        self.cfg = cfg

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname=?", hostname)

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
            searcher.Searcher.where(terms, searchcols), 'NAME', searcher.Searcher.lastModified('timeModified', modified), limit, offset)
        for i, x in enumerate(ids[:]):
            ids[i] = list(x)
            ids[i][2] = searcher.Searcher.truncate(x[2], terms)

        return ids, count

    def createRepos(self, reposPath, hostname, username, password):
        path = os.path.join(reposPath, hostname)
        util.mkdirChain(reposPath)

        repos = EmptyNetworkRepositoryServer(path, None, None, None, {})
        repos.auth.addUser(username, password)
        repos.auth.addAcl(username, None, None, True, False, True)

        repos.auth.addUser("anonymous", "anonymous")
        repos.auth.addAcl("anonymous", None, None, False, False, False)

        # add the mint auth user so we can add additional permissions
        # to this repository
        repos.auth.addUser(self.cfg.authUser, self.cfg.authPass)
        repos.auth.addAcl(self.cfg.authUser, None, None, True, False, True)

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

    def getLabelsForProject(self, projectId):
        cu = self.db.cursor()

        cu.execute("""SELECT labelId, label, url, username, password
                      FROM Labels
                      WHERE projectId=?""", projectId)

        repoMap = {}
        labelIdMap = {}
        for labelId, label, url, username, password in cu:
            labelIdMap[label] = labelId
            host = label[:label.find('@')]
            if url:
                if username and password:
                    urlparts = urlparse.urlparse(url)
                    map = "".join((urlparts[0], "://%s:%s@" % (username, password)) + urlparts[1:])
                else:
                    map = url
            else:
                map = "https://%s/conary/" % (host)

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
                      FROM Profiles p, Labels l
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

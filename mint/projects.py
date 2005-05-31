#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import os
import sys
import time

import sqlite3
from lib import util
from repository.netrepos.netserver import NetworkRepositoryServer

from mint_error import MintError
import database
import userlevels

class InvalidHostname(Exception):
    def __str__(self):
        return "invalid hostname: must start with a letter and contain only letters, numbers, and hyphens."

class Project(database.TableObject):
    __slots__ = ['projectId', 'ownerId', 'name',
                 'desc', 'hostname', 'defaultBranch'
                 'timeCreated', 'timeModified']

    def getItem(self, id):
        return self.server.getProject(id)

    def getOwnerId(self):
        return self.ownerId

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
        return self.server.getProjectUsers(self.id)

    def getUserLevel(self, userId):
        try:
            return self.server.getUserLevel(self.id, userId)
        except database.ItemNotFound:
            return -1

    def addMemberById(self, userId, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, userId, None, level)

    def addMemberByName(self, username, level):
        assert(level in userlevels.LEVELS)
        return self.server.addMember(self.id, None, username, level)

    def delMemberById(self, userId):
        return self.server.delMember(self.id, userId)

class ProjectsTable(database.KeyedTable):
    name = 'Projects'
    key = 'projectId'
    createSQL = """CREATE TABLE Projects (
                    projectId       INTEGER PRIMARY KEY,
                    ownerId         INT,
                    name            STR UNIQUE,
                    hostname        STR UNIQUE,
                    defaultBranch   STR,
                    desc            STR,
                    timeCreated     INT,
                    timeModified    INT
                );"""
    fields = ['ownerId', 'name', 'hostname', 'defaultBranch',
              'desc', 'timeCreated', 'timeModified']

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Projects WHERE hostname=?", hostname)

        try:
            r = cu.next()
        except StopIteration:
            raise database.ItemNotFound
        return r[0]

    def createRepos(self, reposPath, hostname, username, password):
        path = os.path.join(reposPath, hostname)
        util.mkdirChain(reposPath)

        repos = EmptyNetworkRepositoryServer(path, None, None, None, {})
        repos.auth.addUser(username, password)
        repos.auth.addAcl(username, None, None, True, False, True)

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

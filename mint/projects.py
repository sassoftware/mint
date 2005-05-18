#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys
import time
import conary

import sqlite3

from mint_error import MintError
from database import TableObject, DatabaseTable, ItemNotFound

class DuplicateProjectName:
    def __str__(self):
        return "a project with that name already exists"

class Project(TableObject):
    __slots__ = ['projectId', 'userId',
                 'name', 'desc',
                 'timeCreated', 'timeModified']

    def getItem(self, id):
        return self.server.getProject(id)

    def getUserId(self):
        return self.userId

    def getName(self):
        return self.name

    def getDesc(self):
        return self.desc

    def getTimeCreated(self):
        return self.timeCreated

    def getTimeModified(self):
        return self.timeModified

class ProjectsTable(DatabaseTable):
    name = 'Projects'
    key = 'projectId'
    createSQL = """CREATE TABLE Projects (
                    projectId       INTEGER PRIMARY KEY,
                    userId          INT,
                    name            STR UNIQUE,
                    hostname        STR UNIQUE,
                    desc            STR,
                    timeCreated     INT,
                    timeModified    INT
                );"""
    fields = ['userId', 'name', 'desc', 'timeCreated', 'timeModified']

    def getProjectIdByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Repos WHERE hostname=?", hostname)

        try:
            r = cu.next()
        except StopIteration:
            raise ItemNotFound
        return r[0]

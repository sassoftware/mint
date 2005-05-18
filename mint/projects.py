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
from database import TableObject

class DuplicateProjectName:
    def __str__(self):
        return "a project with that name already exists"

class ProjectNotFound:
    def __str__(self):
        return "project not found"

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

class ProjectsTable:
    def __init__(self, db):
        self.db = db

        cu = self.db.cursor()
        cu.execute("SELECT tbl_name FROM sqlite_master WHERE type='table'")
        
        tables = [ x[0] for x in cu ]
        if 'Projects' not in tables:
            cu.execute("""
                CREATE TABLE Projects (
                    projectId       INTEGER PRIMARY KEY,
                    userId          INT,
                    name            STR UNIQUE,
                    desc            STR,
                    timeCreated     INT,
                    timeModified    INT
                );""")

    def newProject(self, name, hostname, userId, desc):
        cu = self.db.cursor()

        try:
            cu.execute("""INSERT INTO Projects VALUES (NULL, ?, ?, ?, ?, 0)""",
                userId, name, desc, time.time())
        except sqlite3.ProgrammingError: # XXX make sure this error is actually duplicated column value
            raise DuplicateProjectName
        else:
            self.db.commit()
        return cu.lastrowid

    def getProject(self, id):
        fields = ['userId', 'name', 'desc', 'timeCreated', 'timeModified']

        cu = self.db.cursor()
        stmt = "SELECT %s FROM Projects WHERE projectId=?" % ", ".join(fields)
        cu.execute(stmt, id)
        try:
            r = cu.next()
        except StopIteration:
            raise ProjectNotFound
        
        data = {}
        for i, key in enumerate(fields):
            data[key] = r[i]
        return data

    def getProjectByHostname(self, hostname):
        cu = self.db.cursor()

        cu.execute("SELECT projectId FROM Repos WHERE hostname=?", hostname)

        try:
            r = cu.next()
        except StopIteration:
            raise ProjectNotFound
        return r[0]

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

class DuplicateProjectName:
    def __str__(self):
        return "a project with that name already exists"

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

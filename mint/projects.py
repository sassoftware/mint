#
# Copyright (c) 2005 rpath, Inc.
#
# All Rights Reserved
#
import sys
import time
import conary

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
                    name            STR,
                    desc            STR,
                    timeCreated     INT,
                    timeModified    INT
                );""")

    def newProject(self, name, hostname, userId, desc):
        cu = self.db.cursor()

        cu.execute("""INSERT INTO Projects VALUES (NULL, ?, ?, ?, ?, 0)""",
            userId, name, desc, time.time())
        self.db.commit()
        return cu.lastrowid

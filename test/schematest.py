#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import tempfile
import time
import os, sys
import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels, server
from mint.distro import jsversion
from conary import dbstore
from conary import sqlite3
from conary.lib import util

sqlite_schema8_tables = \
                      ["""CREATE TABLE DatabaseVersion (
                              version INTEGER PRIMARY KEY,
                              timestamp REAL)""",
                         """CREATE TABLE Labels (
                              labelId         INTEGER PRIMARY KEY,
                              projectId       INT,
                              label           STR,
                              url             STR,
                              username        STR,
                              password        STR)""",
                         """CREATE TABLE Projects (
                              projectId       INTEGER PRIMARY KEY,
                              creatorId       INT,
                              name            STR UNIQUE,
                              hostname        STR UNIQUE,
                              domainname      STR DEFAULT '' NOT NULL,
                              projecturl      STR DEFAULT '' NOT NULL,
                              description     STR NOT NULL DEFAULT '',
                              disabled        INT DEFAULT 0,
                              hidden          INT DEFAULT 0,
                              external        INT DEFAULT 0,
                              timeCreated     INT,
                              timeModified    INT DEFAULT 0)""",
                       """CREATE TABLE Jobs (
                              jobId           INTEGER PRIMARY KEY,
                              releaseId       INT,
                              groupTroveId    INT,
                              userId          INT,
                              status          INT,
                              statusMessage   STR,
                              timeStarted     INT,
                              timeFinished    INT)""",
                       """CREATE TABLE ImageFiles (
                              fileId          INTEGER PRIMARY KEY,
                              releaseId       INT,
                              idx             INT,
                              filename        STR,
                              title           STR DEFAULT ''
                              )""",
                       """CREATE TABLE Users (
                              userId       INTEGER PRIMARY KEY,
                              username        STR UNIQUE,
                              fullName        STR,
                              email           STR,
                              displayEmail    STR DEFAULT "",
                              timeCreated     INT,
                              timeAccessed    INT,
                              active          INT,
                              blurb           STR DEFAULT "")""",
                       """CREATE TABLE Confirmations (
                              userId          INTEGER PRIMARY KEY,
                              timeRequested   INT,
                              confirmation    STR)""",
                       """CREATE TABLE ProjectUsers (
                              projectId       INT,
                              userId          INT,
                              level           INT)""",
                       """CREATE TABLE Releases (
                              releaseId            INTEGER PRIMARY KEY,
                              projectId            INT,
                              name                 STR,
                              description          STR,
                              imageType            INT,
                              troveName            STR,
                              troveVersion         STR,
                              troveFlavor          STR,
                              troveLastChanged     INT,
                              published            INT DEFAULT 0,
                              downloads            INT DEFAULT 0,
                              timePublished        INT)""",
                       """CREATE TABLE PackageIndex (
                              pkgId           INTEGER PRIMARY KEY,
                              projectId       INT,
                              name            STR,
                              version         STR)""",
                       """CREATE TABLE NewsCache (
                              itemId          INTEGER PRIMARY KEY,
                              title           STR,
                              pubDate         INT,
                              content         STR,
                              link            STR,
                              category        STR)""",
                       """CREATE TABLE NewsCacheInfo (
                              age INT, feedLink STR)""",
                       """CREATE TABLE Sessions (
                              sessIdx         INTEGER PRIMARY KEY,
                              sid             STR,
                              data            STR)""",
                       """CREATE TABLE MembershipRequests(
                              projectId       INTEGER,
                              userId          INTEGER,
                              comments        TEXT,
                              PRIMARY KEY(projectId, userId))""",
                       """CREATE TABLE Commits (
                              projectId       INT,
                              timestamp       INT,
                              troveName       STR,
                              version         STR,
                              userId          INT)""",
                       """CREATE TABLE ReleaseData (
                              releaseId       INTEGER,
                              name            CHAR(32),
                              value           TEXT,
                              dataType        INTEGER,
                              PRIMARY KEY(releaseId, name))""",
                       """CREATE TABLE GroupTroves(
                              groupTroveId    INTEGER,
                              projectId       INT,
                              creatorId       INT,
                              recipeName      CHAR(32),
                              upstreamVersion CHAR(128),
                              description     TEXT,
                              timeCreated     INT,
                              timeModified    INT,
                              autoResolve     INT,
                              PRIMARY KEY (groupTroveId))""",
                       """CREATE TABLE GroupTroveItems(
                              groupTroveItemId INTEGER,
                              groupTroveId     INT,
                              creatorId        INT,
                              trvName          CHAR(128),
                              trvVersion       TEXT,
                              trvFlavor        TEXT,
                              subGroup         CHAR(128),
                              versionLock      INT,
                              useLock          INT,
                              instSetLock      INT,
                              PRIMARY KEY (groupTroveItemId))""",
                       """CREATE TABLE JobData (
                              jobId            INTEGER,
                              name             CHAR(32),
                              value            TEXT,
                              dataType         INTEGER,
                              PRIMARY KEY(jobId, name))"""]

mysql_schema8_tables = ["""CREATE TABLE GroupTroveItems(
                              groupTroveItemId INTEGER,
                              groupTroveId     INT,
                              creatorId        INT,
                              trvName          CHAR(128),
                              trvVersion       TEXT,
                              trvFlavor        TEXT,
                              subGroup         CHAR(128),
                              versionLock      INT,
                              useLock          INT,
                              instSetLock      INT,
                              PRIMARY KEY (groupTroveItemId))""",
                        """CREATE TABLE GroupTroves(
                              groupTroveId    INTEGER,
                              projectId       INT,
                              creatorId       INT,
                              recipeName      CHAR(32),
                              upstreamVersion CHAR(128),
                              description     TEXT,
                              timeCreated     INT,
                              timeModified    INT,
                              autoResolve     INT,
                              PRIMARY KEY (groupTroveId))""",
                        """CREATE TABLE JobData (
                              jobId            INTEGER,
                              name             CHAR(32),
                              value            TEXT,
                              dataType         INTEGER,
                              PRIMARY KEY(jobId, name))""",
                        """CREATE TABLE MembershipRequests(
                              projectId       INTEGER,
                              userId          INTEGER,
                              comments        TEXT,
                              PRIMARY KEY(projectId, userId))""",
                        """CREATE TABLE ProjectUsers (
                              projectId       INT,
                              userId          INT,
                              level           INT)""",
                        """CREATE TABLE ReleaseData (
                              releaseId       INTEGER,
                              name            CHAR(32),
                              value           TEXT,
                              dataType        INTEGER,
                              PRIMARY KEY(releaseId, name))""",
                        """CREATE TABLE Sessions (
                              sessIdx    INT PRIMARY KEY AUTO_INCREMENT,
                              sid        VARCHAR(64),
                              data       TEXT)""",
                        """CREATE TABLE Projects (
                              projectId       INT PRIMARY KEY AUTO_INCREMENT,
                              creatorId       INT,
                              name            varchar(128) UNIQUE,
                              hostname        varchar(128) UNIQUE,
                              domainname      varchar(128) DEFAULT '' NOT NULL,
                              projecturl      varchar(128) DEFAULT '' NOT NULL,
                              description     text NOT NULL DEFAULT '',
                              disabled        INT DEFAULT 0,
                              hidden          INT DEFAULT 0,
                              external        INT DEFAULT 0,
                              timeCreated     INT,
                              timeModified    INT DEFAULT 0)""",
                        """CREATE TABLE Labels (
                              labelId         INT PRIMARY KEY AUTO_INCREMENT,
                              projectId       INT,
                              label           VARCHAR(128),
                              url             VARCHAR(128),
                              username        VARCHAR(128),
                              password        VARCHAR(128)
                              )""",
                        """CREATE TABLE Jobs (
                              jobId           INT PRIMARY KEY AUTO_INCREMENT,
                              releaseId       INT,
                              groupTroveId    INT,
                              userId          INT,
                              status          INT,
                              statusMessage   VARCHAR(128),
                              timeStarted     DOUBLE,
                              timeFinished    DOUBLE )""",
                        """CREATE TABLE Releases (
                              releaseId         INT PRIMARY KEY AUTO_INCREMENT,
                              projectId         INT,
                              name              VARCHAR(128),
                              description       VARCHAR(255),
                              imageType         INT,
                              troveName         VARCHAR(128),
                              troveVersion      VARCHAR(255),
                              troveFlavor       VARCHAR(4096),
                              troveLastChanged  INT,
                              published         INT DEFAULT 0,
                              downloads         INT DEFAULT 0,
                              timePublished     INT)""",
                         """CREATE TABLE DatabaseVersion (
                              version INT PRIMARY KEY,
                              timestamp INT)""",
                        """CREATE TABLE Commits (
                              projectId   INT,
                              timestamp   DOUBLE,
                              troveName   VARCHAR(255),
                              version     VARCHAR(255),
                              userId      INT)""",
                        """CREATE TABLE Confirmations (
                              userId          INT PRIMARY KEY AUTO_INCREMENT,
                              timeRequested   DOUBLE,
                              confirmation    VARCHAR(255))""",
                        """CREATE TABLE ImageFiles (
                              fileId      INT PRIMARY KEY AUTO_INCREMENT,
                              releaseId   INT,
                              idx         INT,
                              filename    VARCHAR(255),
                              title       VARCHAR(255) DEFAULT '')""",
                        """CREATE TABLE NewsCacheInfo (
                              age INT,
                              feedLink VARCHAR(255))""",
                        """CREATE TABLE NewsCache (
                              itemId          INT PRIMARY KEY AUTO_INCREMENT,
                              title           VARCHAR(255),
                              pubDate         INT,
                              content         VARCHAR(255),
                              link            VARCHAR(255),
                              category        VARCHAR(255))""",
                        """CREATE TABLE PackageIndex (
                              pkgId       INT PRIMARY KEY AUTO_INCREMENT,
                              projectId   INT,
                              name        VARCHAR(255),
                              version     VARCHAR(255))""",
                        """
                        CREATE TABLE Users (
                              userId          INT PRIMARY KEY AUTO_INCREMENT,
                              username        VARCHAR(255) UNIQUE,
                              fullName        VARCHAR(255),
                              email           VARCHAR(255),
                              displayEmail    VARCHAR(255) DEFAULT "",
                              timeCreated     DOUBLE,
                              timeAccessed    DOUBLE,
                              active          INT,
                              blurb           VARCHAR(255) DEFAULT "")"""]

schema8_indexes = ["""CREATE INDEX DatabaseVersionIdx
                          ON DatabaseVersion(version)""",
                   """CREATE INDEX ProjectsHostnameIdx
                          ON Projects(hostname)""",
                   """CREATE INDEX ProjectsDisabledIdx
                          ON Projects(disabled)""",
                   """CREATE INDEX ProjectsHiddenIdx
                          ON Projects(hidden)""",
                   """CREATE INDEX UsersActiveIdx
                          ON Users(username, active)""",
                   """CREATE INDEX UsersUsernameIdx
                          ON Users(username)""",
                   """CREATE UNIQUE INDEX ProjectUsersIdx
                          ON ProjectUsers(projectId, userId)""",
                   """CREATE INDEX ProjectUsersProjectIdx
                          ON ProjectUsers(projectId)""",
                   """CREATE INDEX ProjectUsersUserIdx
                          ON ProjectUsers(userId)""",
                   """CREATE INDEX ReleaseProjectIdIdx
                          ON Releases(projectId)""",
                   """CREATE INDEX PackageNameIdx
                          ON PackageIndex(name)"""]


class UpgradePathTest(MintRepositoryHelper):
    def testSchemaVerEight(self):
        # Create a database matching schema 8 paradigm.
        # Instantiate table objects on this version and attempt an upgrade.
        # If our upgrade path is right, this test should continue to work
        # forever but new tests may be needed in the future regardless.
        # any time we track truly new information, we'll need a new schema
        # upgrade baseline, especially if that data is mangled during upgrade.

        newAuthRepo = tempfile.mktemp()
        util.copyfile("archive/authdb", newAuthRepo)

        client = self.openMintClient()
        cfg = client.getCfg()
        cfg.authDbPath = newAuthRepo
        authDb = sqlite3.connect(newAuthRepo)

        aCu = authDb.cursor()
        cu = self.db.cursor()

        if cfg.dbDriver == 'sqlite':
            cu.execute("""SELECT name FROM sqlite_master
                              WHERE sql NOT NULL AND type=='table'""")
            for tableName in [x[0] for x in cu.fetchall()]:
                if tableName.startswith('sqlite_'):
                    continue
                cu.execute('DROP TABLE %s' % tableName)

            for tableSql in sqlite_schema8_tables:
                cu.execute(tableSql)
            for indexSql in schema8_indexes:
                cu.execute(indexSql)
        else:
            dbName = cfg.dbPath.split('/')[1]
            cu.execute("DROP DATABASE %s" % dbName)
            cu.execute("CREATE DATABASE %s" % dbName)
            cu.execute("USE %s " % dbName)
            for tableSql in mysql_schema8_tables:
                cu.execute(tableSql)
            for indexSql in schema8_indexes:
                cu.execute(indexSql)

        # create some users
        cu.execute("INSERT INTO Users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   1, 'adminuser', 'Admin User', 'no@email', '',
                   1131751105.57499, 1134485874.74314, 1, '' )
        cu.execute("INSERT INTO Users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   2, 'testuser', 'Test User', 'no@email', '',
                   1131751105.57499, 1134485874.74314, 1, '' )
        cu.execute("INSERT INTO Users VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   3, 'unconf', 'Unconfirmed', 'no@email', '',
                   1131751105.57499, 1134485874.74314, 0, '' )

        cu.execute("INSERT INTO Confirmations VALUES(?, ?, ?)", 3, 0,
                   "confirmation string")

        for userId, userName, salt, passwd in \
                ((3, 'adminuser', '\x03\xd5<\xfa',
                  '2c387d3c22ee7a025703cc09bcde3839'),
                 (4, 'testuser', '\rk4\xa4',
                  '93853a6bd098ca0a1eb6d907fba591a8'),
                 (5, 'unconf', ';\x94\x19(',
                  '083166ffdc02741c8e71d866c6bbf04c'),
                 (7, 'missing', '', '')):
            aCu.execute('INSERT INTO Users VALUES(?, ?, ?, ?)',
                        userId, userName, salt, passwd)
            aCu.execute('INSERT INTO UserGroups VALUES(?, ?)',
                        userId, userName)
            aCu.execute('INSERT INTO UserGroupMembers VALUES(?, ?)',
                        userId, userId)

        aCu.execute("INSERT INTO UserGroups VALUES(6, 'MintAdmin')")
        aCu.execute("INSERT INTO UserGroupMembers VALUES (6,3)")

        # authrepo is using sqlite connection. needs explicit commit.
        authDb.commit()

        # create projects
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   1, 1, 'Foo', 'foo', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   2, 2, 'Bar', 'bar', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   3, 1, 'Baz', 'baz', 'rpath.local', '', '', 0, 0, 0, 0, 0)

        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 1, 1, 0)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 2, 1, 1)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 2, 2, 0)

        # create sessions
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 1, 32*'A', '')
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 2, 32*'B', '')
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 3, 32*'C', '')

        # create releases
        cu.execute("INSERT INTO Releases VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   1, 1, '', '', 1, '', '', '', 0, 0, 3, 0)
        cu.execute("INSERT INTO Releases VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   2, 2, '', '', 1, '', '', '', 0, 0, 3, 0)

        # add some release data
        cu.execute("INSERT INTO ReleaseData VALUES(?, ?, ?, ?)",
                   1, 'jsversion', '1.5.4', 0)

        cu.execute("INSERT INTO ReleaseData VALUES(?, ?, ?, ?)",
                   1, 'skipMediaCheck', '1', 1)

        cu.execute("INSERT INTO GroupTroves VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   1, 1, 1, 'group-test', '0.0.1', '', 0, 0, 1)

        # set version
        cu.execute("INSERT INTO DatabaseVersion VALUES(8, 0)")

        self.db.commit()

        # now create a server object (which will perform the upgrade)
        try:
            fd = os.open(os.devnull, os.W_OK)
            oldStdOut = os.dup(sys.stdout.fileno())
            oldStdErr = os.dup(sys.stderr.fileno())
            os.dup2(fd, sys.stdout.fileno())
            os.dup2(fd, sys.stderr.fileno())
            os.close(fd)
            server.MintServer(cfg, alwaysReload = True)
        finally:
            os.dup2(oldStdOut, sys.stdout.fileno())
            os.dup2(oldStdErr, sys.stderr.fileno())
            # sqlite: since the schema changed we need to reconnect.
            if cfg.dbDriver == "sqlite":
                self.db.dbh.close()
                self.db = dbstore.connect(cfg.dbPath, driver=cfg.dbDriver)
                cu = self.db.cursor()

        ##### past this point: simple sanity checks that the schema upgrade
        # went as planned. fair game for future compatibilty tweaking.
        cu.execute("SELECT salt, passwd FROM Users")

        self.failIf((None, None) in cu.fetchall(),
                    "Some passwords failed to transfer from the authrepo")

        cu.execute("SELECT * FROM UserGroups ORDER BY userGroupId")
        self.failIf([(int(x[0]), x[1]) for x in cu.fetchall()] != \
                    [(1, 'public'), (2, 'mintauth'), (3, 'anonymous'),
                     (4, 'adminuser'), (5, 'testuser'), (6, 'unconf'),
                     (7, 'MintAdmin'), (8, 'missing')],
                    "UserGroups mangled during upgrade process")

        cu.execute("""SELECT * FROM UserGroupMembers
                          ORDER BY userGroupId, userId""")
        self.failIf([(int(x[0]), int(x[1])) for x in cu.fetchall()] \
                    != [(1, 1), (1, 2), (1, 3), (1, 4), (2, 4), (4, 1), (5, 2),
                        (6, 3), (7, 1)],
                    "UserGroupMembers mangled during upgrade process")

        cu.execute("SELECT userId FROM Users WHERE username='public'")
        self.failIf(cu.fetchall(),
                    "Upgrade process introduced a 'public' user account"
                    " (as opposed to a user group only)")

        cu.execute("SELECT IFNULL(MAX(version), 0) FROM DatabaseVersion")
        self.failIf(cu.fetchone()[0] != \
                    client.server._server.version.schemaVersion,
                    "Schema failed to follow complete upgrade path")

        cu.execute("""SELECT releaseId, value FROM ReleaseData
                          WHERE name='showMediaCheck'""")

        self.failIf(cu.fetchone() != (1, '0'),
                    "schema upgrade 14 failed for showMediaCheck.")

        cu.execute("""SELECT releaseId, value FROM ReleaseData
                          WHERE name='skipMediaCheck'""")

        self.failIf(cu.fetchone(),
                    "schema upgrade 14 failed for skipMediaCheck.")

        cu.execute("""SELECT releaseId, value FROM ReleaseData
                          WHERE name='jsversion'""")

        jsVer = jsversion.getDefaultVersion()
        self.failIf(cu.fetchall() != [(1, '1.5.4'), (2, jsVer)],
                    "schema upgrade 15 failed.")

        cu.execute("SELECT * FROM GroupTroves")
        self.failIf(cu.fetchall() != \
                    [(1, 1, 1, 'group-test', '0.0.1', '', 0, 0, 1)],
                    "Accidentally lost group trove entries during upgrade")

        adminClient, adminId = self.quickMintAdmin('admin', 'admin')
        # check to see if a name of the new max size falters.
        adminClient.createGroupTrove(1, 'group-' + ('a' * 194),
                                     '1.0.0', '', True)

    def testSchemaVerFifteen(self):
        # schema test designed to test upgrade codepath for exisiting project
        # repos for rBuilder Schema 15. only tests one schema bump.
        client, userId = self.quickMintUser('testuser', 'testpass')
        client2, userId2 = self.quickMintUser('testuser1', 'testpass')
        projectId = self.newProject(client, 'With Mirror ACL', 'hasMirror')
        projectId2 = self.newProject(client, 'Without Mirror ACL', 'noMirror')
        projectId3 = self.newProject(client, 'Pretend External', 'notThere')
        projectId4 = self.newProject(client, 'Orphaned project', 'orphan')
        projectId5 = self.newProject(client, 'Disabled project', 'disabled')


        project = client.getProject(projectId)
        project.addMemberById(userId2, userlevels.DEVELOPER)

        project2 = client.getProject(projectId2)
        project3 = client.getProject(projectId3)
        project4 = client.getProject(projectId4)
        project4.delMemberById(userId)
        adminClient = self.openMintClient((self.mintCfg.authUser,
                                          self.mintCfg.authPass))
        adminClient.disableProject(projectId5)

        repos = project2.server._server._getProjectRepo(project2)
        repos.setUserGroupCanMirror(project2.getLabel(), self.mintCfg.authUser, 0)

        repos = project3.server._server._getProjectRepo(project3)
        repos.setUserGroupCanMirror(project3.getLabel(), 'testuser', 0)

        assert(self.getMirrorAcl(project, self.mintCfg.authUser) == 1)
        assert(self.getMirrorAcl(project2, self.mintCfg.authUser) == 0)

        #make one project external
        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                   projectId3)

        # force schema 15
        cu.execute("DELETE FROM DatabaseVersion WHERE version > 14")
        cu.execute("INSERT INTO DatabaseVersion VALUES(?, ?)", 15, time.time())
        self.db.commit()

        # do only one iteration of version check
        try:
            fd = os.open(os.devnull, os.W_OK)
            oldStdOut = os.dup(sys.stdout.fileno())
            oldStdErr = os.dup(sys.stderr.fileno())
            os.dup2(fd, sys.stdout.fileno())
            os.dup2(fd, sys.stderr.fileno())
            os.close(fd)
            client.server._server.projects.versionCheck()
        finally:
            os.dup2(oldStdOut, sys.stdout.fileno())
            os.dup2(oldStdErr, sys.stderr.fileno())

        assert(self.getMirrorAcl(project, self.mintCfg.authUser) == 1)
        self.failIf(self.getMirrorAcl(project2, self.mintCfg.authUser) != 1,
                    "schema upgrade didn't correct authUser mirror ACLs")

        self.failIf(self.getMirrorAcl(project, 'testuser') != 1,
                    "schema upgrade didn't correct owner mirror ACLs")

        self.failIf(self.getMirrorAcl(project, 'testuser1'),
                    "schema upgrade incorrectly added mirror ACL to developer")

        self.failIf(self.getMirrorAcl(project3, 'testuser') == 1,
                    "schema upgrade tried to update external project.")


if __name__ == "__main__":
    testsuite.main()

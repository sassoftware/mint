#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import tempfile
import time
import os, sys
import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import userlevels, server
from mint import jsversion
from mint import buildtypes
from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.lib import util

# NOTE: ReleaseImageTypes was created much later than schema 8,
# but was subsequently deleted during a schema upgrade. in order for
# the upgrade to pass, we need to insert it.

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
                              PRIMARY KEY(jobId, name))""",
                       """CREATE TABLE ReleaseImageTypes (
                              releaseId   INT,
                              imageType   INT,
                              PRIMARY KEY (releaseId, imageType))""",
                        """CREATE TABLE InboundLabels (
                                projectId       INT NOT NULL,
                                labelId         INT NOT NULL,
                                url             VARCHAR(255),
                                username        VARCHAR(255),
                                password        VARCHAR(255),
                                CONSTRAINT InboundLabels_projectId_fk
                                    FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
                                CONSTRAINT InboundLabels_labelId_fk
                                    FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE)""",
                        """CREATE TABLE OutboundLabels (
                                projectId       INT NOT NULL,
                                labelId         INT NOT NULL,
                                url             VARCHAR(255),
                                username        VARCHAR(255),
                                password        VARCHAR(255),
                                CONSTRAINT OutboundLabels_projectId_fk
                                    FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
                                CONSTRAINT OutboundLabels_labelId_fk
                                    FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE)""",
                       """CREATE TABLE OutboundMatchTroves (
                            projectId       INT NOT NULL,
                            labelId         INT NOT NULL,
                            idx             INT NOT NULL,
                            matchStr         VARCHAR(255),
                            CONSTRAINT OutboundMatchTroves_projectId_fk
                                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                ON DELETE RESTRICT ON UPDATE CASCADE,
                            CONSTRAINT OutboundMatchTroves_labelId_fk
                                FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                ON DELETE RESTRICT ON UPDATE CASCADE) """ ]

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
                              blurb           VARCHAR(255) DEFAULT "")""",
                        """CREATE TABLE ReleaseImageTypes (
                              releaseId   INT,
                              imageType   INT,
                              PRIMARY KEY (releaseId, imageType))""",
                        """CREATE TABLE InboundLabels (
                                projectId       INT NOT NULL,
                                labelId         INT NOT NULL,
                                url             VARCHAR(255),
                                username        VARCHAR(255),
                                password        VARCHAR(255),
                                CONSTRAINT InboundLabels_projectId_fk
                                    FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
                                CONSTRAINT InboundLabels_labelId_fk
                                    FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE)""",
                        """CREATE TABLE OutboundLabels (
                                projectId       INT NOT NULL,
                                labelId         INT NOT NULL,
                                url             VARCHAR(255),
                                username        VARCHAR(255),
                                password        VARCHAR(255),
                                CONSTRAINT OutboundLabels_projectId_fk
                                    FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE,
                                CONSTRAINT OutboundLabels_labelId_fk
                                    FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                    ON DELETE RESTRICT ON UPDATE CASCADE)""",
                       """CREATE TABLE OutboundMatchTroves (
                            projectId       INT NOT NULL,
                            labelId         INT NOT NULL,
                            idx             INT NOT NULL,
                            matchStr         VARCHAR(255),
                            CONSTRAINT OutboundMatchTroves_projectId_fk
                                FOREIGN KEY (projectId) REFERENCES Projects(projectId)
                                ON DELETE RESTRICT ON UPDATE CASCADE,
                            CONSTRAINT OutboundMatchTroves_labelId_fk
                                FOREIGN KEY (labelId) REFERENCES Labels(labelId)
                                ON DELETE RESTRICT ON UPDATE CASCADE) """ ]

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
    def forceSchemaVersion(self, version):
        cu = self.db.cursor()
        cu.execute("DELETE FROM DatabaseVersion WHERE version > ?", version - 1)
        cu.execute("INSERT INTO DatabaseVersion VALUES(?, ?)", version,
                   time.time())
        self.db.commit()

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
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   1, 1, 'foo.rpath.local@rpl:devel',
                   'http://foo.rpath.local/conary', 'mintauth', 'mintpass')
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   2, 2, 'Bar', 'bar', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   2, 2, 'bar.rpath.local@rpl:devel',
                   'http://bar.rpath.local/conary', 'mintauth', 'mintpass')
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   3, 1, 'Baz', 'baz', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   3, 3, 'baz.rpath.local@rpl:devel',
                   'http://baz.rpath.local/conary', 'mintauth', 'mintpass')

        # external project (for inbound mirroring)
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   4, 1, 'quux', 'quux', 'rpath.local', '', '', 0, 0, 1, 0, 0)
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   4, 4, 'quux.rpath.local@rpl:devel',
                   'http://quux.rpath.local/conary', 'mintauth', 'mintpass')

        # internal project (for outbound mirroring)
        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   5, 1, 'fooz', 'fooz', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   5, 5, 'fooz.rpath.local@rpl:devel',
                   'http://fooz.rpath.local/conary', 'mintauth', 'mintpass')

        cu.execute("INSERT INTO Projects VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   6, 1, 'blarch', 'blarch', 'rpath.local', '', '', 0, 0, 0, 0, 0)
        cu.execute("INSERT INTO Labels VALUES(?,?,?,?,?,?)",
                   6, 6, 'blarch.rpath.local@rpl:devel',
                   'http://blarch.rpath.local/conary', 'mintauth', 'mintpass')

        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 1, 1, 0)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 2, 1, 1)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 2, 2, 0)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 4, 1, 0)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 5, 1, 0)
        cu.execute("INSERT INTO ProjectUsers VALUES(?, ?, ?)", 6, 1, 0)

        # create sessions
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 1, 32*'A', '')
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 2, 32*'B', '')
        cu.execute("INSERT INTO Sessions VALUES(?, ?, ?)", 3, 32*'C', '')

        # create releases
        cu.execute("INSERT INTO Releases VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   1, 1, '', '', 1, '',
                   '/foo.rpath.local@rpl:devel/0.0:1.0.0-1-1',
                   '', 0, 0, 3, 0)
        cu.execute("INSERT INTO Releases VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   2, 2, '', '', 1, '',
                   '/foo.rpath.local@rpl:devel/0.0:1.0.1-1-1',
                   '', 0, 0, 3, 0)
        cu.execute("INSERT INTO Releases VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                   3, 2, 'pub', 'pub rel', 1, '',
                   '/foo.rpath.local@rpl:devel/0.0:1.0.2-1-1', '',
                   0, 1, 3, 5000)

        cu.execute("INSERT INTO ImageFiles VALUES(?, ?, ?, ?, ?)",
                   1, 3, 1, 'foo', 'Test File')

        # add some release data
        cu.execute("INSERT INTO ReleaseData VALUES(?, ?, ?, ?)",
                   1, 'jsversion', '1.5.4', 0)

        cu.execute("INSERT INTO ReleaseData VALUES(?, ?, ?, ?)",
                   1, 'skipMediaCheck', '1', 1)

        cu.execute("INSERT INTO GroupTroves VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
                   1, 1, 1, 'group-test', '0.0.1', '', 0, 0, 1)


        # insert mirroring information
        cu.execute("INSERT INTO InboundLabels VALUES(?,?,?,?,?)",
                4, 4, 'http://www.elsewhere.com/conary', 'somebody', 'somepass')
        cu.execute("INSERT INTO OutboundLabels VALUES(?,?,?,?,?)",
                5, 5, 'http://www.inbound.com/conary', 'dontguess', 'meplease')

        cu.execute("INSERT INTO OutboundLabels VALUES(?,?,?,?,?)",
                6, 6, 'http://www.mooz.com/conary', 'egghead', 'beaniebot')

        cu.execute("INSERT INTO OutboundMatchTroves VALUES(?,?,?,?)",
                5, 5, 0, '-.*:source$')
        cu.execute("INSERT INTO OutboundMatchTroves VALUES(?,?,?,?)",
                5, 5, 1, '-.*:debuginfo$')
        cu.execute("INSERT INTO OutboundMatchTroves VALUES(?,?,?,?)",
                5, 5, 2, '+.*')

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

        # schema upgrade 20 converted the name release to build
        cu.execute("""SELECT buildId, value FROM BuildData
                          WHERE name='showMediaCheck'""")

        self.failIf(cu.fetchone() != (1, '0'),
                    "schema upgrade 14 failed for showMediaCheck.")

        cu.execute("""SELECT buildId, value FROM BuildData
                          WHERE name='skipMediaCheck'""")

        self.failIf(cu.fetchone(),
                    "schema upgrade 14 failed for skipMediaCheck.")

        cu.execute("""SELECT buildId, value FROM BuildData
                          WHERE name='jsversion'""")

        jsVer = jsversion.getDefaultVersion()
        self.failIf(cu.fetchall() != [(1, '1.5.4'), (2, jsVer), (3L, jsVer)],
                    "schema upgrade 15 failed.")

        cu.execute("SELECT * FROM GroupTroves")
        self.failIf(cu.fetchall() != \
                    [(1, 1, 1, 'group-test', '0.0.1', '', 0, 0, 1)],
                    "Accidentally lost group trove entries during upgrade")

        adminClient, adminId = self.quickMintAdmin('admin', 'admin')
        # check to see if a name of the new max size falters.
        adminClient.createGroupTrove(1, 'group-' + ('a' * 194),
                                     '1.0.0', '', True)

        cu.execute('SELECT * FROM Builds')
        self.failIf(cu.fetchall() != \
                    [(1L, 1L, None, None, '', '', '',
                      '/foo.rpath.local@rpl:devel/0.0:1.0.0-1-1', '',
                      0L, None, None, None, None, 0),
                     (2L, 2L, None, None, '', '', '',
                      '/foo.rpath.local@rpl:devel/0.0:1.0.1-1-1', '',
                      0L, None, None, None, None, 0),
                     (3L, 2L, 3L, None, 'pub', 'pub rel', '',
                      '/foo.rpath.local@rpl:devel/0.0:1.0.2-1-1', '',
                      0L, None, None, None, None, 0)],
                    "Schema upgrade 20 failed for release to build conversion")

        cu.execute('SELECT * FROM PublishedReleases')
        self.failIf(cu.fetchall() != \
                    [(3L, 2L, 'pub', '1.0.2', 'pub rel', None, None, None,
                      None, 5000, None)],
                    'Schema upgrade 20 failed for pub release creation')

        cu.execute("SELECT * FROM BuildFiles")
        self.failIf(cu.fetchall() != \
                    [(1, 3, 1, 'foo', 'Test File', None, None)],
                    "Schema upgrade 20 didn't migrate build files correctly")

        cu.execute("SELECT * FROM InboundMirrors")
        self.failUnlessEqual(cu.fetchall(),
                [(1, 4, 'quux.rpath.local@rpl:devel', 'http://www.elsewhere.com/conary', 'somebody', 'somepass')],
                "Schema 25 upgrade didn't migrate InboundLabels")

        cu.execute("SELECT * FROM OutboundMirrors")
        self.failUnlessEqual(cu.fetchall(),
                [(1, 5, 'fooz.rpath.local@rpl:devel', 'http://www.inbound.com/conary', 'dontguess', 'meplease', 0, 0, '-.*:source$ -.*:debuginfo$ +.*'),
                 (2, 6, 'blarch.rpath.local@rpl:devel', 'http://www.mooz.com/conary', 'egghead', 'beaniebot', 0, 0, '')],
                "Schema 25 upgrade didn't migrate OutboundLabels")


    def testSchemaVerFifteen(self):
        # schema test designed to test upgrade codepath for exisiting project
        # repos for rBuilder Schema 15. only tests one schema bump.
        client, userId = self.quickMintUser('testuser', 'testpass')
        client2, userId2 = self.quickMintUser('testuser1', 'testpass')
        projectId = self.newProject(client, 'With Mirror ACL', 'hasMirror')
        projectId2 = self.newProject(client, 'Without Mirror ACL', 'noMirror')
        projectId3 = self.newProject(client, 'Pretend External', 'notThere')
        projectId4 = self.newProject(client, 'Orphaned project', 'orphan')

        project = client.getProject(projectId)
        project.addMemberById(userId2, userlevels.DEVELOPER)

        project2 = client.getProject(projectId2)
        project3 = client.getProject(projectId3)
        project4 = client.getProject(projectId4)
        project4.delMemberById(userId)
        adminClient = self.openMintClient((self.mintCfg.authUser,
                                          self.mintCfg.authPass))

        repos = project2.server._server._getProjectRepo(project2)
        repos.setUserGroupCanMirror(versions.Label(project2.getLabel()), self.mintCfg.authUser, 0)

        repos = project3.server._server._getProjectRepo(project3)
        repos.setUserGroupCanMirror(versions.Label(project3.getLabel()), 'testuser', 0)

        assert(self.getMirrorAcl(project, self.mintCfg.authUser) == 1)
        assert(self.getMirrorAcl(project2, self.mintCfg.authUser) == 0)

        #make one project external
        cu = self.db.cursor()
        cu.execute("UPDATE Projects SET external=1 WHERE projectId=?",
                   projectId3)

        self.forceSchemaVersion(15)

        self.captureAllOutput(client.server._server.projects.versionCheck)
        self.db.commit()

        assert(self.getMirrorAcl(project, self.mintCfg.authUser) == 1)
        self.failIf(self.getMirrorAcl(project2, self.mintCfg.authUser) != 1,
                    "schema upgrade didn't correct authUser mirror ACLs")

        self.failIf(self.getMirrorAcl(project, 'testuser') != 1,
                    "schema upgrade didn't correct owner mirror ACLs")

        self.failIf(self.getMirrorAcl(project, 'testuser1'),
                    "schema upgrade incorrectly added mirror ACL to developer")

        self.failIf(self.getMirrorAcl(project3, 'testuser') == 1,
                    "schema upgrade tried to update external project.")

    def testSchemaVer23(self):
        # tests the upgrade path for VMware image's disk adapter only
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        build = client.newBuild(projectId, 'Control Build')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "Test Title"]])

        build = client.newBuild(projectId, 'VMware Build')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "Test Title"]])
        build.setBuildType(buildtypes.VMWARE_IMAGE)

        cu = self.db.cursor()
        cu.execute("SELECT * FROM BuildData WHERE name = 'diskAdapter'")
        self.failIf(cu.fetchall(),
                     "diskAdapter upgrade baseline needs tweaking. check test.")

        self.forceSchemaVersion(23)
        client.server._server.buildData.versionCheck()
        client.server._server.buildData.db.commit()

        cu = self.db.cursor()
        cu.execute("SELECT * FROM BuildData WHERE name = 'diskAdapter'")
        self.failUnlessEqual(cu.fetchall(), [(2, 'diskAdapter', 'ide', 0)],
                     "diskAdapter upgrade failed")

    def testSchemaVer25(self):
        # tests the upgrade path for VMware image's snapshotting settings only
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        build = client.newBuild(projectId, 'Control Build')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "Test Title"]])

        build = client.newBuild(projectId, 'VMware Build')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        build.setFiles([["file1", "Test Title"]])
        build.setBuildType(buildtypes.VMWARE_IMAGE)

        self.failIf(build.getDataValue('vmSnapshots'),
                    "vmSnapshots baseline incorrect")

        cu = self.db.cursor()
        cu.execute("SELECT * FROM BuildData WHERE name = 'vmSnapshots'")
        self.failIf(cu.fetchall(),
                     "vmSnapshots upgrade baseline needs tweaking. check test.")

        self.forceSchemaVersion(25)
        client.server._server.buildData.versionCheck()
        client.server._server.buildData.db.commit()

        cu = self.db.cursor()
        cu.execute("SELECT * FROM BuildData WHERE name = 'vmSnapshots'")
        self.failUnlessEqual(cu.fetchall(), [(2, 'vmSnapshots', '1', 1)],
                     "vmSnapshots upgrade failed")

        build.refresh()
        self.failIf(not build.getDataValue('vmSnapshots'),
                    "vmSnapshots data value behaves incorrectly")

    def testDbBumpVersion(self):
        client, userId = self.quickMintAdmin('admin', 'passwd')
        cu = self.db.cursor()
        cu.execute('SELECT MAX(version) FROM DatabaseVersion')
        assert cu.fetchone()[0] == client.server._server.version.schemaVersion
        client.server._server.version.bumpVersion()
        # ensure bumping version does not exceed max schema version
        cu.execute('SELECT MAX(version) FROM DatabaseVersion')
        assert cu.fetchone()[0] == client.server._server.version.schemaVersion


if __name__ == "__main__":
    testsuite.main()

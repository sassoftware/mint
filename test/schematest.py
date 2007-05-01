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
from mint import buildtypes
from mint import mirror
from conary import dbstore
from conary import sqlite3
from conary import versions
from conary.lib import util


class UpgradePathTest(MintRepositoryHelper):
    def forceSchemaVersion(self, version):
        cu = self.db.cursor()
        cu.execute("DELETE FROM DatabaseVersion WHERE version > ?", version - 1)
        cu.execute("INSERT INTO DatabaseVersion VALUES(?, ?)", version,
                   time.time())
        self.db.commit()

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

    def testSchemaVersionThirtyFour(self):
        # create a project and and admin user
        client, userId = self.quickMintAdmin('admin', 'admin')
        projectIds = []
        projectIds.append(self.newProject(client, "test 1", "test1"))
        projectIds.append(self.newProject(client, "test 2", "test2"))

        # recreate old OutboundMirrors table structure
        self.forceSchemaVersion(34)

        cu = self.db.cursor()
        cu.execute("DROP TABLE OutboundMirrorTargets")
        cu.execute("DROP TABLE OutboundMirrors")
        cu.execute("DROP TABLE Projects")
        cu.execute("""CREATE TABLE OutboundMirrors (
                outboundMirrorId %(PRIMARYKEY)s,
                sourceProjectId  INT NOT NULL,
                targetLabels     VARCHAR(767) NOT NULL,
                targetUrl        VARCHAR(767) NOT NULL,
                targetUsername   VARCHAR(254),
                targetPassword   VARCHAR(254),
                allLabels        INT NOT NULL DEFAULT 0,
                recurse          INT NOT NULL DEFAULT 0,
                matchStrings     VARCHAR(767) NOT NULL DEFAULT '',
                mirrorOrder      INT DEFAULT 0,
                CONSTRAINT OutboundMirrors_sourceProjectId_fk
                    FOREIGN KEY (sourceProjectId) REFERENCES Projects(projectId)
                    ON DELETE CASCADE ON UPDATE CASCADE
            ) %(TABLEOPTS)s""" % self.db.keywords)

        cu.execute("""INSERT INTO OutboundMirrors
            VALUES(1, ?, 'test1.elsewhere.com@rpl:mirror',
                'http://mirror.elsewhere.com/conary/',
                'mirrorUser', 'mirrorPassword', 0, 0,
                '', 0)""", projectIds[0])
        cu.execute("""INSERT INTO OutboundMirrors
            VALUES(2, ?, 'test2.elsewhere.com@rpl:mirror',
                'http://mirror.elsewhere.com/conary/',
                'mirrorUser', 'mirrorPassword', 1, 0,
                ?, 1)""", projectIds[1],
                ' '.join(mirror.EXCLUDE_SOURCE_MATCH_TROVES))
        self.db.commit()

        # trigger migration
        newServer = server.MintServer(self.mintCfg, alwaysReload = True)
        if self.mintCfg.dbDriver == 'sqlite':
            self.db.dbh.close()
            self.db = dbstore.connect(self.mintCfg.dbPath,
                    self.mintCfg.dbDriver)
        #client.server._server = newServer
        client = self.openMintClient(('admin', 'admin'))

        om = client.getOutboundMirror(1)
        omTargets = client.getOutboundMirrorTargets(1)

        self.assertEqual(om['targetLabels'],
                "test1.elsewhere.com@rpl:mirror")
        self.assertEqual(om['allLabels'], 0)
        self.assertEqual(len(omTargets), 1)
        self.assertEqual(omTargets[0][1],
                'http://mirror.elsewhere.com/conary/')
        om = client.getOutboundMirror(2)
        omTargets = client.getOutboundMirrorTargets(2)

        self.assertEqual(om['targetLabels'],
                "test2.elsewhere.com@rpl:mirror")
        self.assertEqual(om['allLabels'], 1)
        self.assertEqual(len(omTargets), 1)
        self.assertEqual(omTargets[0][1],
                'http://mirror.elsewhere.com/conary/')
        self.assertEqual(client.getOutboundMirrorMatchTroves(1), [])
        self.assertEqual(client.getOutboundMirrorMatchTroves(2),
                mirror.EXCLUDE_SOURCE_MATCH_TROVES)

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

#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#


import fixtures

from mint.scripts import pkgindexer

from conary import dbstore

class PkgIndexTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)

    def tearDown(self):
        fixtures.FixturedUnitTest.tearDown(self)

    @fixtures.fixture("Full")
    def testUpdateMarkLocal(self, db, data):
        client = self.getClient("user")
        upi = pkgindexer.UpdatePackageIndexExternal( \
                aMintServer = client.server._server)
        db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        upi.db = db
        upi.updateMark()
        cu = db.cursor()
        cu.execute("SELECT * FROM PackageIndexMark")
        self.assertEquals(cu.fetchone()[0], 0)

    @fixtures.fixture("Empty")
    def testUpdateMarkExt(self, db, data):
        client = self.getClient("user")
        upi = pkgindexer.UpdatePackageIndexExternal( \
                aMintServer = client.server._server)
        db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        upi.db = db
        upi.updateMark()
        cu = db.cursor()
        cu.execute("SELECT * FROM PackageIndexMark")
        self.assertEquals(cu.fetchone()[0], 1)

    @fixtures.fixture("Full")
    def testUpdateNoMarkLocal(self, db, data):
        client = self.getClient("user")
        upi = pkgindexer.UpdatePackageIndexExternal( \
                aMintServer = client.server._server)
        db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        cu = db.cursor()
        cu.execute("DELETE FROM PackageIndexMark")
        db.commit()
        upi.db = db
        upi.updateMark()
        cu.execute("SELECT * FROM PackageIndexMark")
        # local project present, so nothing should be done to the mark,
        # even if it was missing
        self.assertEquals(cu.fetchone(), None)

    @fixtures.fixture("Empty")
    def testUpdateNoMarkExt(self, db, data):
        client = self.getClient("user")
        upi = pkgindexer.UpdatePackageIndexExternal( \
                aMintServer = client.server._server)
        db = dbstore.connect(self.cfg.dbPath, driver = self.cfg.dbDriver)
        cu = db.cursor()
        cu.execute("DELETE FROM PackageIndexMark")
        db.commit()
        upi.db = db
        upi.updateMark()
        cu.execute("SELECT * FROM PackageIndexMark")
        # no local projects, so mark should be set to 1, even if it was gone
        self.assertEquals(cu.fetchone()[0], 1)



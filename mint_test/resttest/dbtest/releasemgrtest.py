#!/usr/bin/python
import testsetup
from testutils import mock

from mint import mint_error
from mint.lib import data

from mint import buildtypes

from mint.rest import errors
from mint.rest.api import models

import mint_rephelp

class ReleaseManagerTest(mint_rephelp.MintDatabaseHelper):
    def testListReleasesForProduct(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        imageId2 = self.createImage(db, 'foo', buildtypes.TARBALL)
        self.setImageFiles(db, 'foo', imageId2)
        releaseId = db.createRelease('foo', 'Release 1', 'desc1', [imageId])
        releaseId2 = db.createRelease('foo', 'Release 2', 'desc2', [imageId2])
        releases = db.listReleasesForProduct('foo').releases
        release1 = [ x for x in releases if x.releaseId == releaseId ][0]
        release2 = [ x for x in releases if x.releaseId == releaseId2 ][0]
        assert(release1.creator == 'admin')
        assert(release1.name == 'Release 1')
        assert(release1.timePublished == None)
        assert(release1.publisher == None)
        assert(release2.creator == 'admin')
        assert(release2.name == 'Release 2')
        db.publishRelease('foo', releaseId, True)
        releases = db.listReleasesForProduct('foo').releases
        release1 = [ x for x in releases if x.releaseId == releaseId ][0]
        assert(release1.publisher == 'admin')
        assert(release1.timePublished)
        assert(release1.shouldMirror == 1)

    def testGetReleaseForProduct(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        imageId2 = self.createImage(db, 'foo', buildtypes.TARBALL)
        self.setImageFiles(db, 'foo', imageId2)
        releaseId = db.createRelease('foo', 'Release 1', 'desc1', [imageId])
        release1 = db.getReleaseForProduct('foo', releaseId)
        assert(release1.creator == 'admin')
        assert(release1.name == 'Release 1')
        assert(release1.timePublished == None)
        assert(release1.publisher == None)
        db.publishRelease('foo', releaseId, True)
        release1 = db.getReleaseForProduct('foo', releaseId)
        assert(release1.publisher == 'admin')
        assert(release1.timePublished)
        assert(release1.shouldMirror == 1)
        self.createProduct('bar', db=db)
        self.assertRaises(errors.ReleaseNotFound,
                          db.getReleaseForProduct, 'bar', releaseId)
       
    def testCreateReleaseErrors(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('user')
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db, users=['user'])
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        # try to add an empty build to a release.
        self.assertRaises(mint_error.BuildEmpty,
                          db.createRelease, 'foo', 'Release 1', 'desc1', [imageId])
        self.setImageFiles(db, 'foo', imageId)
        db.createRelease('foo', 'Release 1', 'desc1', [imageId])
        # try to add a build to two releases.
        self.assertRaises(mint_error.BuildPublished,
                          db.createRelease, 'foo', 'Release 2', 'desc2', [imageId])
        # don't have permissions to create a release.
        # imageId is not in the right project.
        imageId = self.createImage(db, 'foo', buildtypes.TARBALL)
        self.setImageFiles(db, 'foo', imageId)
        self.setDbUser(db, 'user')
        self.assertRaises(errors.PermissionDenied,
                          db.createRelease, 'foo', 'Release 2', 'desc2', [imageId])

    def testPublishUnpublishRelease(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        releaseId = db.createRelease('foo', 'Release 1', 'desc1', [imageId])
        mock.mockMethod(db.releaseMgr.publisher.notify)
        db.publishRelease('foo', releaseId, True)
        db.releaseMgr.publisher.notify._mock.assertCalled('ReleasePublished', releaseId)
        release = db.getReleaseForProduct('foo', releaseId)
        assert(release.timePublished)
        assert(release.shouldMirror)
        assert(release.publisher == 'admin')
        db.unpublishRelease('foo', releaseId)
        release = db.getReleaseForProduct('foo', releaseId)
        assert(not release.timePublished)
        assert(not release.shouldMirror)
        assert(not release.publisher)

    def testPublishReleaseErrors(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db)
        self.createProduct('bar', db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        releaseId = db.createRelease('foo', 'Release 1', 'desc1', [imageId])
        # release is not in the right project.
        self.assertRaises(errors.ReleaseNotFound,
                          db.publishRelease, 'bar', releaseId, False)
        # release is already published
        db.publishRelease('foo', releaseId, False)
        self.assertRaises(mint_error.PublishedReleasePublished,
                          db.publishRelease,'foo', releaseId, False)
        self.assertRaises(errors.ReleaseNotFound,
                          db.unpublishRelease, 'bar', releaseId)
        db.unpublishRelease('foo', releaseId)
        self.assertRaises(mint_error.PublishedReleaseNotPublished,
                          db.unpublishRelease, 'foo', releaseId)
        releaseId = db.createRelease('foo', 'Release 2', 'desc2', [])
        self.assertRaises(mint_error.PublishedReleaseEmpty,
                          db.publishRelease, 'foo', releaseId, False)

testsetup.main()

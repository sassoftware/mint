#!/usr/bin/python
import testsetup
from testutils import mock

from mint import mint_error
from mint.lib import data

from mint import buildtypes

from mint.rest import errors
from mint.rest.api import models

from mint_test import mint_rephelp

class Settings(object):
    def __init__(self, d):
        self.__dict__.update(d)

class ReleaseManagerTest(mint_rephelp.MintDatabaseHelper):

    @mint_rephelp.restFixturize('dbtest.setupImages')
    def setupImages(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createUser('user')
        self.setDbUser(db, 'admin')
        self.createProduct('foo', db=db, users=['user'])
        self.createProduct('bar', db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        imageId2 = self.createImage(db, 'foo', buildtypes.TARBALL)
        self.setImageFiles(db, 'foo', imageId2)
        emptyImageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        releaseId = db.createRelease('foo', 'Release 1', 'desc1', '1.0',
                                     [imageId])
        return Settings(locals())

    def testListReleasesForProduct(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        self.setDbUser(db, 'admin')
        releaseId2 = db.createRelease('foo', 'Release 2', 'desc2', '2.0',
                                      [data.imageId2])
        releases = db.listReleasesForProduct('foo').releases
        release1 = [ x for x in releases if x.releaseId == data.releaseId ][0]
        release2 = [ x for x in releases if x.releaseId == releaseId2 ][0]
        assert(release1.creator == 'admin')
        assert(release1.name == 'Release 1')
        assert(release1.timePublished == None)
        assert(release1.publisher == None)
        assert(release2.creator == 'admin')
        assert(release2.name == 'Release 2')
        db.publishRelease('foo', data.releaseId, True)
        releases = db.listReleasesForProduct('foo').releases
        release1 = [ x for x in releases if x.releaseId == data.releaseId ][0]
        assert(release1.publisher == 'admin')
        assert(release1.timePublished)
        assert(release1.shouldMirror == 1)

    def testDeleteRelease(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        image = db.getImageForProduct('foo', data.imageId)
        assert(image.release == data.releaseId)
        db.deleteRelease('foo', data.releaseId)
        image = db.getImageForProduct('foo', data.imageId)
        assert(image.release is None)

    def testUpdateRelease(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        imageIds = [ x.imageId for x in
                     db.listImagesForRelease('foo', data.releaseId).images ]
        assert(imageIds == [data.imageId])
        db.updateRelease('foo', data.releaseId, 'Updated Name', 'updated desc',
                          'updated version', None, None, [data.imageId2])
        release = db.getReleaseForProduct('foo', data.releaseId)
        assert(release.name == 'Updated Name')
        assert(release.description == 'updated desc')
        assert(release.version == 'updated version')
        imageIds = [ x.imageId for x in
                     db.listImagesForRelease('foo', data.releaseId).images ]
        assert(imageIds == [data.imageId2])

    def testGetReleaseForProduct(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        release1 = db.getReleaseForProduct('foo', data.releaseId)
        assert(release1.creator == 'admin')
        assert(release1.name == 'Release 1')
        assert(release1.timePublished == None)
        assert(release1.publisher == None)
        self.setDbUser(db, 'admin')
        db.publishRelease('foo', data.releaseId, True)
        release1 = db.getReleaseForProduct('foo', data.releaseId)
        assert(release1.publisher == 'admin')
        assert(release1.timePublished)
        assert(release1.shouldMirror == 1)
        self.assertRaises(errors.ReleaseNotFound,
                          db.getReleaseForProduct, 'bar', data.releaseId)

    def testCreateReleaseErrors(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        # try to add an empty build to a release.
        self.assertRaises(mint_error.BuildEmpty,
                          db.createRelease, 'foo', 'Release 1', 'desc1', 'v1',
                          [data.emptyImageId])
        # try to add a build to two releases.
        self.assertRaises(mint_error.BuildPublished,
                          db.createRelease, 'foo', 'Release 2', 
                          'desc2', 'v1', [data.imageId])
        # don't have permissions to create a release.
        self.setDbUser(db, 'user')
        self.assertRaises(errors.PermissionDeniedError,
                          db.createRelease, 'foo', 'Release 2',
                          'desc2', 'v1', [data.imageId2])
        # imageId is not in the right project.

    def testPublishUnpublishRelease(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        self.setDbUser(db, 'admin')
        mock.mockMethod(db.releaseMgr.publisher.notify)
        db.publishRelease('foo', data.releaseId, True)
        db.releaseMgr.publisher.notify._mock.assertCalled('ReleasePublished',
                data.releaseId)
        release = db.getReleaseForProduct('foo', data.releaseId)
        assert(release.timePublished)
        assert(release.shouldMirror)
        assert(release.publisher == 'admin')
        db.unpublishRelease('foo', data.releaseId)
        release = db.getReleaseForProduct('foo', data.releaseId)
        assert(not release.timePublished)
        assert(not release.shouldMirror)
        assert(not release.publisher)

    def testPublishReleaseErrors(self):
        data = self.setupImages()
        db = self.openMintDatabase(createRepos=False)
        # release is not in the right project.
        self.assertRaises(errors.ReleaseNotFound,
                          db.publishRelease, 'bar', data.releaseId, False)
        # release is already published
        db.publishRelease('foo', data.releaseId, False)
        self.assertRaises(mint_error.PublishedReleasePublished,
                          db.publishRelease,'foo', data.releaseId, False)
        # unpublish not in the right project
        self.assertRaises(errors.ReleaseNotFound,
                          db.unpublishRelease, 'bar', data.releaseId)
        db.unpublishRelease('foo', data.releaseId)

        # unpublish not published
        self.assertRaises(mint_error.PublishedReleaseNotPublished,
                          db.unpublishRelease, 'foo', data.releaseId)

        # publish empty release
        releaseId = db.createRelease('foo', 'Release 2', 'desc2', 'v1', [])
        self.assertRaises(mint_error.PublishedReleaseEmpty,
                          db.publishRelease, 'foo', releaseId, False)

testsetup.main()

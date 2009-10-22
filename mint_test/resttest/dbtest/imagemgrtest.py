#!/usr/bin/python
import testsetup
from testutils import mock

from conary.lib import cfgtypes

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint.lib import data

from mint.rest import errors
from mint.rest.db import imagemgr

from mint_test import mint_rephelp

class ImageManagerTest(mint_rephelp.MintDatabaseHelper):
    
    def testListImagesForProduct(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProduct('foo2', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                troveFlavor='is: x86')
        self.setImageFiles(db, 'foo', imageId)
        self.createImage(db, 'foo2', buildtypes.INSTALLABLE_ISO,
                troveFlavor='is: sparc sparc64')
        image, = db.listImagesForProduct('foo').images
        self.failUnlessEqual(str(image),
            "models.Image(1, 'installableIsoImage', 'foo=/localhost@test:1/0.1-1-1[is: x86]')")
        image, = db.listImagesForProduct('foo2').images
        self.failUnlessEqual(image.imageId, 2)
        self.failUnlessEqual(image.hostname, 'foo2')
        self.failUnlessEqual(image.architecture, 'sparc64')

    def testListImagesForRelease(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   name='Image1')
        self.setImageFiles(db, 'foo', imageId)
        imageId2 = self.createImage(db, 'foo', buildtypes.AMI, 
                                    name='Image2')
        self.createImage(db, 'foo', buildtypes.TARBALL, name='Image3')
        self.setImageFiles(db, 'foo', imageId2)
        releaseId = db.createRelease('foo', 'name', '', 'v1', [imageId, imageId2])
        images = db.listImagesForRelease('foo', releaseId).images
        assert(len(images) == 2)
        images = dict((x.name, x) for x in images)
        image1 = images['Image1']
        image2 = images['Image2']
        assert(image1.imageId == imageId)
        assert(image2.imageId == imageId2)

    def testListImagesForTrove(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   name='Image1', troveName='group-foo')
        imageId2 = self.createImage(db, 'foo', buildtypes.AMI, 
                                    name='Image2', troveName='group-foo')
        imageId3 = self.createImage(db, 'foo', buildtypes.AMI, 
                                    name='Image2', troveName='group-bar')
        image = db.getImageForProduct('foo', imageId)
        troveTuple = image.getNameVersionFlavor()
        images = db.listImagesForTrove('foo', *troveTuple).images
        assert(len(images) == 2)
        assert(set(x.imageId for x in images) == set([imageId, imageId2]))

    def testListImagesForProductVersion(self):
        db = self.openMintDatabase()
        self.createUser('admin', admin=True)
        self.setDbUser(db, 'admin')
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', namespace='rpl')
        hostname = 'foo.%s' % mint_rephelp.MINT_PROJECT_DOMAIN
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                           name='Image1', troveName='group-foo',
                           troveVersion='/%s@rpl:foo-1/1.0:1.0-1' % hostname)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                           name='Image1', troveName='group-foo',
                       troveVersion='/%s@rpl:foo-1-devel/1.0:1.0-1' % hostname)
        images = db.listImagesForProductVersion('foo', '1').images
        assert(len(images) == 2)
        images = db.listImagesForProductVersionStage('foo', '1', 'Release').images
        assert(len(images) == 1)

    def testListFilesForImage(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   name='Image1')
        self.setImageFiles(db, 'foo', imageId)
        file, = db.listFilesForImage('foo', imageId).files
        self.assertEqual(file.sha1, '356a192b7913b04c54574d18c28d46e6395428ab')
        self.assertEqual(file.size, 1024)
        self.assertEqual(file.title, 'Image File 1')
        self.assertEqual(len(file.urls), 1)
        self.assertEqual(file.urls[0].fileId, 1)
        self.assertEqual(file.urls[0].urlType, 0)

    def testAddImageStatus(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   name='Image1')
        self.setImageFiles(db, 'foo', imageId)
        image = db.getImageForProduct('foo', imageId)
        imageMgr = imagemgr.ImageManager(self.mintCfg, db, db.auth)
        self.assertEqual(image.imageStatus.code, jobstatus.RUNNING)
        self.assertEqual(image.imageStatus.message, 'foo')
        self.assertEqual(image.imageStatus.isFinal, False)

        # No job + image files -> finished
        image.imageStatus.set_status(jobstatus.WAITING)
        imageMgr._updateStatusForImageList([image])
        self.failUnlessEqual(image.imageStatus.code, jobstatus.FINISHED)
        self.failUnlessEqual(image.imageStatus.message, 'Finished')
        self.failUnlessEqual(image.imageStatus.isFinal, True)

        # No job + no image files -> failed
        image.imageStatus.set_status(jobstatus.WAITING)
        image.files.files = []
        imageMgr._updateStatusForImageList([image])
        self.failUnlessEqual(image.imageStatus.code, jobstatus.FAILED)
        self.failUnlessEqual(image.imageStatus.message, 'Error')
        self.failUnlessEqual(image.imageStatus.isFinal, True)

        # Imageless build -> finished
        image.imageStatus.set_status(jobstatus.WAITING)
        mock.mockMethod(image.hasBuild, False)
        imageMgr._updateStatusForImageList([image])
        self.failUnlessEqual(image.imageStatus.code, jobstatus.FINISHED)
        self.failUnlessEqual(image.imageStatus.message, 'Finished')
        self.failUnlessEqual(image.imageStatus.isFinal, True)

    def testCreateImage(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                               troveFlavor='xen, domU',
                               buildData=[('foo', 'bar', data.RDT_STRING)])
        found, value = db.db.buildData.getDataValue(imageId, 'foo')
        assert(found)
        assert(value == 'bar')
        found, value = db.db.buildData.getDataValue(imageId, 'XEN_DOMU')
        assert(found)
        assert(value == 1)

    def testSetImageFiles(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)

        db.setImageFiles('foo', imageId, [('filename1', 'title')])
        files = db.getImageForProduct('foo', imageId).files.files
        self.assertEqual(len(files), 1)
        file, = files
        self.assertEqual(file.title, 'title')
        self.assertEqual(file.urls[0].fileId, 1)
        self.assertEqual(file.urls[0].urlType, 0)

        db.setImageFiles('foo', imageId, [('filename2', 'title2', 1024, 'sha')])
        files = db.getImageForProduct('foo', imageId).files.files
        self.assertEqual(len(files), 1)
        file, = files
        self.assertEqual(file.title, 'title2')
        self.assertEqual(file.urls[0].fileId, 2)
        self.assertEqual(file.urls[0].urlType, 0)
        self.assertEqual(file.size, 1024)
        self.assertEqual(file.sha1, 'sha')
        self.assertRaises(ValueError,
                db.setImageFiles, 'foo', imageId, 
                                 [('filename2', 'title2', 1024)])
        
testsetup.main()

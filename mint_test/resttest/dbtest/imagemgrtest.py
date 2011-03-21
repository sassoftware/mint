#!/usr/bin/python
import testsetup
from testutils import mock

from conary.lib import cfgtypes

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint.lib import data

from mint.rest import errors
from mint.rest.api import models
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

        # Try the ordering both ways
        imageIds = [ imageId, imageId2 ]
        ret = db.imageMgr._getFilesForImages('hostName', imageIds)
        self.failUnlessEqual([x.imageId for x in ret ], imageIds)

        imageIds.reverse()
        ret = db.imageMgr._getFilesForImages('hostName', imageIds)
        self.failUnlessEqual([x.imageId for x in ret ], imageIds)

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

    def testListImagesByType(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   troveFlavor="is: x86", name='Image1')
        self.setImageFiles(db, 'foo', imageId)

        self.createProduct('bar', owners=['admin'], db=db)
        imageId = self.createImage(db, 'bar', buildtypes.INSTALLABLE_ISO,
                                   troveFlavor="is: x86_64", name='Image1')
        self.setImageFiles(db, 'bar', imageId)

        # Add a target
        targetType = 'vmware'
        targetName = 'abc.eng.rpath.com'
        db.targetMgr.addTarget(targetType, targetName, dict(alias=targetName,
            description=targetName))

        # Add some fake target images
        tgtImageIds = [ 'vmware-image-id-1', 'vmware-image-id-2' ]
        for targetImageId in tgtImageIds:
            db.targetMgr.linkTargetImageToImage(targetType, targetName,
                imageId, targetImageId)
            # Add it twice, to make sure duplicates are removed
            db.targetMgr.linkTargetImageToImage(targetType, targetName,
                imageId, targetImageId)

        images = db.imageMgr.getAllImagesByType('INSTALLABLE_ISO')
        self.failUnlessEqual(
            [ x['architecture'] for x in images ],
            [ 'x86', 'x86_64'])
        self.failUnlessEqual(
            [ [ x['sha1'] for x in img['files'] ] for img in images],
            [ [ '356a192b7913b04c54574d18c28d46e6395428ab' ],
              [ 'da4b9237bacccdf19c0760cab7aec4a8359010b0' ] ])
        self.failUnlessEqual(
            [ [ x['targetImages'] for x in img['files'] ] for img in images],
            [
                [[]],
                [[
                    ('vmware', 'abc.eng.rpath.com', 'vmware-image-id-1'),
                    ('vmware', 'abc.eng.rpath.com', 'vmware-image-id-2'),
                ]]])

        # RBL-6290: make sure we don't have cross-polination of hostnames
        self.failUnlessEqual(
            [ img['baseFileName'] for img in images ],
            [ 'foo-0.1-x86', 'bar-0.1-x86_64', ])
        self.failUnlessEqual(
            [ [ x['fileName'] for x in img['files'] ] for img in images],
            [ [ 'imagefile_1.iso' ], [ 'imagefile_2.iso' ] ])
        self.failUnlessEqual(
            [ [ x['downloadUrl'] for x in img['files'] ] for img in images],
            [ [ 'https://test.rpath.local:0/downloadImage?fileId=1', ],
              [ 'https://test.rpath.local:0/downloadImage?fileId=2', ] ])

    def testAddImageStatus(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                name='Image1',
                buildData=[('outputToken', 'abcdef', data.RDT_STRING)])

        # Initial creation -> unknown
        image = db.getImageForProduct('foo', imageId)
        self.assertEqual(image.imageStatus.code, jobstatus.UNKNOWN)
        self.assertEqual(image.imageStatus.message, '')
        self.assertEqual(image.imageStatus.isFinal, False)

        # Set by build machinery
        status = models.ImageStatus(code=jobstatus.RUNNING, message='wait plz')
        db.setImageStatus('foo', imageId, 'abcdef', status)

        image = db.getImageForProduct('foo', imageId)
        self.assertEqual(image.imageStatus.code, jobstatus.RUNNING)
        self.assertEqual(image.imageStatus.message, 'wait plz')
        self.assertEqual(image.imageStatus.isFinal, False)

        status = models.ImageStatus(code=jobstatus.FINISHED, message='Is good!')
        db.setImageStatus('foo', imageId, 'abcdef', status)

        image = db.getImageForProduct('foo', imageId)
        self.assertEqual(image.imageStatus.code, jobstatus.FINISHED)
        self.assertEqual(image.imageStatus.message, 'Is good!')
        self.assertEqual(image.imageStatus.isFinal, True)

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
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                buildData=[('outputToken', 'abcdef', data.RDT_STRING)])

        imageFiles = models.ImageFileList(files=[models.ImageFile(
            fileName='filename2', title='title2', size=1024, sha1='sha')])
        db.setFilesForImage('foo', imageId, 'abcdef', imageFiles)

        file, = db.getImageForProduct('foo', imageId).files.files
        self.assertEqual(file.title, 'title2')
        self.assertEqual(file.urls[0].fileId, 1)
        self.assertEqual(file.urls[0].urlType, 0)
        self.assertEqual(file.size, 1024)
        self.assertEqual(file.sha1, 'sha')

    def testSetImageFilesLarge(self):
        """File size over 2 ** 31 shouldn't crash python-pgsql"""
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                buildData=[('outputToken', 'abcdef', data.RDT_STRING)])

        imageFiles = models.ImageFileList(files=[models.ImageFile(
            fileName='filename2', title='title2', size=(2 ** 32),
            sha1='sha')])
        db.setFilesForImage('foo', imageId, 'abcdef', imageFiles)

        file, = db.getImageForProduct('foo', imageId).files.files
        self.assertEqual(file.title, 'title2')
        self.assertEqual(file.urls[0].fileId, 1)
        self.assertEqual(file.urls[0].urlType, 0)
        self.assertEqual(file.size, 2 ** 32)
        self.assertEqual(file.sha1, 'sha')


testsetup.main()

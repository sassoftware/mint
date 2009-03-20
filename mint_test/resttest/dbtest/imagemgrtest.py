#!/usr/bin/python
import testsetup
from testutils import mock

from conary.lib import cfgtypes

from mcp import client as mcpclient
from mcp import mcp_error

from mint import buildtypes
from mint import jobstatus
from mint import mint_error
from mint.lib import data

from mint.rest import errors
from mint.rest.db import imagemgr

import mint_rephelp

class ImageManagerTest(mint_rephelp.MintDatabaseHelper):
    
    def testListImagesForProduct(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProduct('foo2', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO)
        self.setImageFiles(db, 'foo', imageId)
        self.createImage(db, 'foo2', buildtypes.INSTALLABLE_ISO)
        image, = db.listImagesForProduct('foo').images
        assert(str(image) == 
           "models.Image(1, 'Inst CD/DVD', 'foo=/localhost@test:1/0.1-1-1[]')")
        image, = db.listImagesForProduct('foo2').images
        assert(image.imageId == 2)
        assert(image.hostname == 'foo2')
        
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
        releaseId = self.createRelease(db, 'foo', 'name', '', [imageId, imageId2])
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
        self.createProduct('foo', owners=['admin'], db=db)
        self.createProductVersion(db, 'foo', '1', namespace='rpl')
        hostname = 'foo.%s' % mint_rephelp.MINT_PROJECT_DOMAIN
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                           name='Image1', troveName='group-foo',
                           troveVersion='/%s@rpl:foo-1/0:1.0-1' % hostname)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                           name='Image1', troveName='group-foo',
                       troveVersion='/%s@rpl:foo-1-devel/0:1.0-1' % hostname)
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
        assert(file.sha1 == '356a192b7913b04c54574d18c28d46e6395428ab')
        assert(file.size == 1024)
        assert(file.title == 'Image File 1')
        assert(str(file) == 'images.ImageId(fileId=1, size=1024)')
        assert(str(file.urls[0]) == "images.FileUrl(url='%s/images/foo/1/imagefile_1.iso', urlType=0)" % self.workDir)

    def testAddImageStatus(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        self.createProduct('foo', owners=['admin'], db=db)
        imageId = self.createImage(db, 'foo', buildtypes.INSTALLABLE_ISO,
                                   name='Image1')
        self.setImageFiles(db, 'foo', imageId)
        image = db.getImageForProduct('foo', imageId)
        imageMgr = imagemgr.ImageManager(self.mintCfg, db, db.auth)
        imageMgr.mcpClient = mock.MockObject()
        imageMgr.mcpClient.jobStatus._mock.setDefaultReturn(('xx', 'foo'))
        imageMgr._addImageStatus(image)
        assert(image.status == 'xx')
        assert(image.statusMessage == 'foo')
        imageMgr.mcpClient.jobStatus._mock.raiseErrorOnAccess(
                                mcp_error.NetworkError)
        imageMgr._addImageStatus(image)
        assert(image.status == jobstatus.NO_JOB)
        assert(image.statusMessage == jobstatus.statusNames[jobstatus.NO_JOB])
        mock.mockMethod(image.hasBuild, False)
        imageMgr._addImageStatus(image)
        assert(image.status == jobstatus.FINISHED)
        assert(image.statusMessage == jobstatus.statusNames[jobstatus.FINISHED])

    def testGetMcpClient(self):
        db = self.openMintDatabase(createRepos=False)
        self.createUser('admin', admin=True)
        imageMgr = imagemgr.ImageManager(self.mintCfg, db, db.auth)
        mock.mock(mcpclient, 'MCPClientConfig')
        mock.mock(mcpclient, 'MCPClient')
        imageMgr._getMcpClient()
        mcpclient.MCPClientConfig._mock.assertCalled()
        mcpclient.MCPClientConfig().read._mock.assertCalled(
                                self.mintCfg.dataPath + '/mcp/client-config')
        mcpclient.MCPClient._mock.assertCalled(mcpclient.MCPClientConfig())
        assert(imageMgr.mcpClient)
        imageMgr.mcpClient = None
        mcpclient.MCPClientConfig().read._mock.raiseErrorOnAccess(
                                    cfgtypes.CfgEnvironmentError('foo', 'msg'))
        imageMgr._getMcpClient()
        assert(imageMgr.mcpClient)

    def testGetJobServerVersion(self):
        db = self.openMintDatabase(createRepos=False)
        imageMgr = db.imageMgr
        assert(db.imageMgr._getJobServerVersion() == '1.0')
        imageMgr.mcpClient.getJSVersion._mock.raiseErrorOnAccess(
                                            mcp_error.NotEntitledError)
        self.assertRaises(mint_error.NotEntitledError,
                          imageMgr._getJobServerVersion)
        imageMgr.mcpClient.getJSVersion._mock.raiseErrorOnAccess(
                                                mcp_error.NetworkError)
        self.assertRaises(mint_error.BuildSystemDown,
                          imageMgr._getJobServerVersion)

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
        assert(len(files) == 1)
        file, = files
        assert(file.title == 'title')
        assert(file.urls[0].url == 'filename1')
        db.setImageFiles('foo', imageId, [('filename2', 'title2', 1024, 'sha')])
        files = db.getImageForProduct('foo', imageId).files.files
        assert(len(files) == 1)
        file, = files
        assert(file.title == 'title2')
        assert(file.urls[0].url == self.mintCfg.imagesPath + 'foo/1/filename2')
        assert(file.size == 1024)
        assert(file.sha1 == 'sha')
        self.assertRaises(ValueError,
                db.setImageFiles, 'foo', imageId, 
                                 [('filename2', 'title2', 1024)])
        
testsetup.main()

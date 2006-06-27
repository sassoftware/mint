#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import os
import sys
import time

from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import producttypes, producttemplates
from mint.data import RDT_STRING, RDT_BOOL, RDT_INT
from mint.database import ItemNotFound
from mint.distro import installable_iso, jsversion
from mint.mint_error import ProductPublished, ProductMissing, ProductEmpty
from mint.products import ProductDataNameError
from mint.server import deriveBaseFunc, ParameterError

from conary.lib import util
from conary.repository.errors import TroveNotFound

import fixtures

class ProductTest(fixtures.FixturedUnitTest):
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        assert(product.getName() == "Test Product")
        product.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        assert(product.getTrove() ==\
            ('group-trove',
             '/conary.rpath.com@rpl:devel/0.0:1.0-1-1', '1#x86'))
        assert(product.getTroveName() == 'group-trove')
        assert(product.getTroveVersion().asString() == \
               '/conary.rpath.com@rpl:devel/1.0-1-1')
        assert(product.getTroveFlavor().freeze() == '1#x86')
        assert(product.getArch() == "x86")

        product.setFiles([["file1", "File Title 1"],
                          ["file2", "File Title 2"]])
        assert(product.getFiles() ==\
            [{'fileId': 1, 'filename': 'file1',
              'title': 'File Title 1', 'size': 0,},
             {'fileId': 2, 'filename': 'file2',
              'title': 'File Title 2', 'size': 0,}]
        )

        assert(product.getDefaultName() == 'group-trove=1.0-1-1')

        desc = 'Just some random words'
        product.setDesc(desc)
        product.refresh()
        assert desc == product.getDesc()

    @fixtures.fixture("Full")
    def testProductData(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        productType = producttypes.INSTALLABLE_ISO
        product.setProductType(productType)
        assert(productType == product.productType)
        dataTemplate = product.getDataTemplate()
        assert('showMediaCheck' in dataTemplate)
        assert('autoResolve' in dataTemplate)
        assert('freespace' not in dataTemplate)

        rDict = product.getDataDict()
        tDict = product.getDataTemplate()
        for key in tDict:
            assert(tDict[key][1] == rDict[key])

        # test behavior of booleans
        for mediaCheck in (False, True):
            product.setDataValue('showMediaCheck', mediaCheck)
            assert (product.getDataValue('showMediaCheck') is mediaCheck)

        # test bad name lockdown
        self.assertRaises(ProductDataNameError,
            product.setDataValue, 'undefinedName', 'test string')
        self.assertRaises(ProductDataNameError,
                          product.getDataValue, 'undefinedName')

        # test bad name with validation override
        product.setDataValue('undefinedName', 'test string',
            dataType = RDT_STRING, validate = False)
        assert('test string' == product.getDataValue('undefinedName'))

        # test bad name with validation override and no data type specified
        self.assertRaises(ProductDataNameError,
            product.setDataValue, 'undefinedName', None, False)

        product.setProductType(producttypes.STUB_IMAGE)

        # test string behavior
        product.setDataValue('stringArg', 'foo')
        assert('foo' == product.getDataValue('stringArg'))
        product.setDataValue('stringArg', 'bar')
        assert('bar' == product.getDataValue('stringArg'))

        # test int behavior
        for intArg in range(0,3):
            product.setDataValue('intArg', intArg)
            assert(intArg == product.getDataValue('intArg'))

        # test enum behavior
        for enumArg in range(3):
            product.setDataValue('enumArg', str(enumArg))
            assert(str(enumArg) == product.getDataValue('enumArg'))

        # ensure invalid enum values are not accepted.
        self.assertRaises(ParameterError, product.setDataValue, 'enumArg', '5')

    @fixtures.fixture("Full")
    def testMaxIsoSize(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        productType = producttypes.INSTALLABLE_ISO
        product.setProductType(productType)

        for size in ('681574400', '734003200', '4700000000', '8500000000'):
            product.setDataValue('maxIsoSize', size)
            self.failIf(product.getDataValue('maxIsoSize') != size,
                        "size was mangled in xml-rpc")

        self.assertRaises(ParameterError, product.setDataValue, 'maxIsoSize',
                          '10000000')

        maxIsoSize = product.getDataDict()['maxIsoSize']
        self.failIf(maxIsoSize != '8500000000',
                    "Data dict contained %s of %s but expected %s of type str"\
                    % (str(maxIsoSize), str(type(maxIsoSize)), '8500000000'))

    @fixtures.fixture("Full")
    def testMissingProductData(self, db, data):
        # make sure productdata properly returns the default value
        # if the row is missing. this will handle the case of a modified
        # productdata template with old products in the database.

        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        product.setProductType(producttypes.INSTALLABLE_ISO)
        assert(product.getProductType() == [producttypes.INSTALLABLE_ISO])
        assert(product.getDataTemplate()['showMediaCheck'])
        assert(product.getDataTemplate()['autoResolve'])
        try:
            product.getDataTemplate()['freespace']
        except KeyError, e:
            pass
        else:
            self.fail("getDataTemplate returned bogus template data")

        db.cursor().execute("DELETE FROM ProductData WHERE name='bugsUrl'")
        db.commit()

        assert(product.getDataValue("bugsUrl") == "http://issues.rpath.com/")

    @fixtures.fixture("Full")
    def testPublished(self, db, data):
        # FIXME: this is totally broken
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        product.setProductType(producttypes.STUB_IMAGE)
        product.setFiles([["file1", "File Title 1"]])
        product.setPublished(True)

        # refresh
        product = client.getProduct(product.id)

        self.assertRaises(ProductPublished, product.setDataValue,
                          'stringArg', 'bar')

        self.assertRaises(ProductPublished, product.setProductType,
                          producttypes.STUB_IMAGE)

        self.assertRaises(ProductPublished, product.setFiles, list())


        self.assertRaises(ProductPublished, product.setTrove,
                          'Some','Dummy','Args')

        self.assertRaises(ProductPublished, product.setDesc, 'Not allowed')

        self.assertRaises(ProductPublished, product.setPublished, True)

        self.assertRaises(ProductPublished, product.setPublished, False)

        self.assertRaises(ProductPublished, client.startImageJob,
                          product.getId())

        self.failIf(product.getPublished() is not True,
                    "Result of getPublished is not boolean")

    @fixtures.fixture("Full")
    def testDeleteProduct(self, db, data):
        # FIXME: broken w/r/t new release arch
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        product.setProductType(producttypes.STUB_IMAGE)
        product.setFiles([["file1", "File Title 1"]])
        product.setPublished(True)

        try:
            product.deleteProduct()
            self.fail("Product could be deleted after it was published")
        except ProductPublished:
            pass

    @fixtures.fixture("Full")
    def testMissingProduct(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])

        # make a product and delete it, to emulate a race condition
        # from the web UI
        productId = product.getId()
        product.deleteProduct()

        # messing with that same product should now fail in a controlled
        # manner. no UnknownErrors allowed!
        try:
            product.setProductType(producttypes.STUB_IMAGE)
            self.fail("Allowed to set imgage type of a deleted product")
        except ProductMissing:
            pass

        try:
            product.deleteProduct()
            self.fail("Allowed to delete a deleted product")
        except ProductMissing:
            pass

        # nasty hack. unwrap the product data value so that we can attack
        # codepaths not normally allowed by client code.
        setProductDataValue = deriveBaseFunc(client.server._server.setProductDataValue)

        try:
            setProductDataValue(client.server._server, productId, 'someKey', 'someVal', RDT_STRING)
            self.fail("Allowed to set data for a deleted product")
        except ProductMissing:
            pass

        try:
            product.setDesc('some string')
            self.fail("Allowed to set description for a deleted product")
        except ProductMissing:
            pass

        fixtures.stockProductFlavor(db, product.getId())

        try:
            client.startImageJob(productId)
            self.fail("Allowed to start a job for a deleted product")
        except ProductMissing:
            pass

    @fixtures.fixture("Full")
    def testDownloadIncrementing(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        assert(product.getDownloads() == 0)
        product.incDownloads()
        product.refresh()
        assert(product.getDownloads() == 1)

    @fixtures.fixture("Empty")
    def testUnfinishedProduct(self, db, data):
        client = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        brokenProduct = client.newProduct(projectId, "Test Product")
        brokenProductId = brokenProduct.getId()
        # because the first product is not yet finished, creating a new
        # product before finishing it should kill the first.
        product = client.newProduct(projectId, "Test Product")
        productId = product.getId()

        cu = db.cursor()
        cu.execute("SELECT COUNT(*) FROM Products")
        if cu.fetchone()[0] != 1:
            self.fail("Previous unfinished products should be removed")

        cu.execute("UPDATE Products SET troveLastChanged=1")
        db.commit()

        product = client.newProduct(projectId, "Test Product")

        cu.execute("SELECT COUNT(*) FROM Products")
        if cu.fetchone()[0] != 2:
            self.fail("Finished product was deleted")

    @fixtures.fixture("Empty")
    def testUnfinishedProductData(self, db, data):
        client = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        brokenProduct = client.newProduct(projectId, "Test Product")

        cu = db.cursor()
        assert(brokenProduct.getDataValue('jsversion') == \
               jsversion.getDefaultVersion())
        # because the first product is not yet finished, creating a new
        # product before finishing it should kill the first.
        product = client.newProduct(projectId, "Test Product")

        # ensure product data gets cleaned up automatically too.
        self.assertRaises(ProductDataNameError,
                          brokenProduct.getDataValue, 'jsversion')

    @fixtures.fixture("Full")
    def testProductStatus(self, db, data):
        client = self.getClient("owner")
        productId = data['productId']

        if client.server.getProductStatus(productId) != {'status': 5,
                                                         'message': 'No Job',
                                                         'queueLen': 0}:
            self.fail("getProductStatus returned unknown values")

    @fixtures.fixture("Empty")
    def testGetProductsForProjectOrder(self, db, data):
        # FIXME broken w/r/t new release arch
        client = self.getClient("test")
        projectId = client.newProject("Foo", "foo", "rpath.org")

        product = client.newProduct(projectId, 'product 1')
        product.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        product.setFiles([["file1", "File Title 1"]])
        product.setPublished(True)

        # ugly hack. mysql does not distinguish sub-second time resolution
        time.sleep(1)

        product = client.newProduct(projectId, 'product 2')
        product.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        product.setFiles([["file1", "File Title 1"]])
        product.setPublished(True)

        self.failIf(client.server.getProductsForProject(projectId) != [2, 1],
                    "getProductsForProject is not ordered by "
                    "'most recent first'")

    @fixtures.fixture("Full")
    def testPublishEmptyProduct(self, db, data):
        # FIXME broken w/r/t new release arch
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])

        try:
            product.setPublished(True)
        except ProductEmpty:
            pass
        else:
            self.fail("mint_error.ProductEmpty exception expected")

        product.setFiles([["file1", "File Title 1"]])
        product.setPublished(True)

    @fixtures.fixture("Full")
    def testHasVMwareImage(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])

        assert(product.hasVMwareImage() == False)

        product.setFiles([["test.vmware.zip", "Test Image"]])
        assert(product.hasVMwareImage() == True)

    @fixtures.fixture("Full")
    def testGetDisplayTemplates(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])

        self.failIf([(x[0], x[2]) for x in product.getDisplayTemplates()] != \
                    [x for x in producttemplates.dataTemplates.iteritems()],
                    "dataTemplates lost in display translation")

    @fixtures.fixture("Full")
    def testFreespace(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])

        product.setProductType(producttypes.RAW_FS_IMAGE)

        self.failIf(not isinstance(product.getDataValue('freespace'), int),
                    "freespace is not an integer")

        product.setDataValue('freespace', 10, RDT_INT)

        self.failIf(not isinstance(product.getDataValue('freespace'), int),
                    "freespace is not an integer")

class OldProductTest(MintRepositoryHelper):
    def testProductList(self):
        # FIXME broken w/r/t new release arch
        client, userId = self.quickMintUser("testuser", "testpass")
        adminClient, adminuserId = self.quickMintAdmin("adminauth", "adminpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        project2Id = client.newProject("Bar", "bar", "rpath.org")
        project3Id = adminClient.newProject("Hide", "hide", "rpath.org")
        adminClient.hideProject(project3Id)
        productsToMake = [ (int(projectId), "foo", "Foo Unpublished"),
                           (int(project3Id), "hide", "Hide Product 1"),
                           (int(projectId), "foo", "Foo Product"),
                           (int(projectId), "foo", "Foo Product 2"),
                           (int(project2Id), "bar", "Bar Product"),
                           (int(project2Id), "bar", "Bar Product 2"),
                           (int(projectId), "foo", "Foo Product 3")]
        for projId, hostname, relName in productsToMake:
            if "Hide" in relName:
                product = adminClient.newProduct(projId, relName)
            else:
                product = client.newProduct(projId, relName)
            product.setTrove("group-trove", "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
            if "Unpublished" not in relName:
                product.setFiles([["file1", "File Title 1"]])
                product.setPublished(True)
            time.sleep(1) # hack: let the timestamp increment since mysql doesn't do sub-second resolution
        productList = client.getProductList(20, 0)
        productsToMake.reverse()
        hostnames = [x[1] for x in productsToMake]
        if len(productList) != 5:
            self.fail("getProductList returned the wrong number of results")
        for i in range(len(productList)):
            if tuple(productsToMake[i]) != (productList[i][2].projectId, hostnames[i], productList[i][2].name):
                self.fail("Ordering of most recent products is broken.")
            if productList[i][2].projectId == project3Id:
                self.fail("Should not have listed hidden product")

        project = client.getProject(projectId)
        for rel in project.getProducts():
            if rel.getId() not in (3, 4, 7):
                self.fail("getProductsForProject returned incorrect results")

        try:
            client.server.getProductsForProject(project3Id)
        except ItemNotFound, e:
            pass
        else:
            self.fail("getProductsForProject returned hidden products in non-admin context when it shouldn't have")

        project = adminClient.getProject(project3Id)
        rel = project.getProducts()
        if len(rel) != 1:
            self.fail("getProductsForProject did not return hidden products for admin")

    def makeInstallableIsoCfg(self):
        mintDir = os.environ['MINT_PATH']
        os.mkdir("%s/changesets" % self.tmpDir)
        util.mkdirChain("%s/templates/x86/PRODUCTNAME" % self.tmpDir)
        util.mkdirChain("%s/templates/x86_64/PRODUCTNAME" % self.tmpDir)

        cfg = installable_iso.IsoConfig()
        cfg.configPath = self.tmpDir
        cfg.scriptPath = mintDir + "/scripts/"
        cfg.cachePath = self.tmpDir + "/changesets/"
        cfg.anacondaImagesPath = "/dev/null"
        cfg.templatePath = self.tmpDir + "/templates/"
        cfg.SSL = False

        cfgFile = open(cfg.configPath + "/installable_iso.conf", 'w')
        cfg.display(cfgFile)
        cfgFile.close()

        return cfg

    def testHiddenIsoGen(self):
        raise testsuite.SkipTestException("needs to be reworked or abandoned")
        # set up a dummy isogen cfg to avoid importing from
        # job-server (the job-server code should be put elsewhere someday...)
        from conary.conarycfg import ConfigFile
        class IsoGenCfg(ConfigFile):
            imagesPath = self.tmpDir
            configPath = self.tmpDir
            SSL = False

        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        adminClient, adminId = self.quickMintAdmin("adminuser", "adminpass")
        adminClient.hideProject(projectId)

        product = client.newProduct(projectId, 'product 1')
        product.setProductType(producttypes.INSTALLABLE_ISO)
        product.setTrove("group-core",
                         "/testproject." + MINT_PROJECT_DOMAIN + \
                                 "@rpl:devel/0.0:1.0-1-1",
                         "1#x86")

        self.stockProductFlavor(product.getId())

        job = client.startImageJob(product.id)

        cfg = self.makeInstallableIsoCfg()
        imageJob = installable_iso.InstallableIso(client, IsoGenCfg(), job,
                                                  product, project)
        imageJob.isocfg = cfg

        # getting a trove not found from a trove that's really not there isn't
        # terribly exciting. historically this call generated a Permission
        # Denied exception for hidden projects, triggered by the great
        # repoMap/user split.
        cwd = os.getcwd()
        os.chdir(self.tmpDir + "/images")

        # unforutanatel imageJob.write call can be noisy on stderr
        oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)

        try:
            self.assertRaises(TroveNotFound, imageJob.write)
        finally:
            os.dup2(oldFd, sys.stderr.fileno())
            os.close(oldFd)
            os.chdir(cwd)


if __name__ == "__main__":
    testsuite.main()

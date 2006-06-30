#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import time

import fixtures
from mint_rephelp import MINT_HOST, MINT_DOMAIN, MINT_PROJECT_DOMAIN

from mint import producttypes
from mint import pubreleases
from mint.mint_error import PermissionDenied, ProductPublished, ProductMissing, ProductEmpty
from mint.database import ItemNotFound

class PublishedReleaseTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testPublishedReleaseCreation(self, db, data):

        # The full fixture actually creates a published release; we'll
        # use this already created object as a starting point.
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubReleaseId = pubRelease.id
        self.failUnless(pubRelease.id == pubRelease.pubReleaseId,
                "id and pubReleaseId should be identical")

        # check the timeCreated and createdBy fields
        # fixture creates the published release using the owner's id
        self.failUnless(pubRelease.timeCreated > 0, "timeCreated not set")
        self.failUnless(pubRelease.createdBy == data['owner'])

    @fixtures.fixture("Full")
    def testAddProductToPublishedRelease(self, db, data):

        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        project = client.getProject(data['projectId'])
        product = client.getProduct(data['productId'])
        product.setProductType(producttypes.STUB_IMAGE)
        product.setFiles([["file", "file title 1"]])

        # sanity checks
        self.failIf(data['productId'] in pubRelease.getProducts(),
                "Product is not published yet")
        self.failUnless(data['productId'] in project.getUnpublishedProducts(),
                "Product should be in the unpublished list")

        # publish it now
        pubRelease.addProduct(product.id)

        # check the state of the world after publishing
        self.failUnless(data['productId'] in pubRelease.getProducts(),
                "Product was not properly added to published releases")
        self.failIf(data['productId'] in project.getUnpublishedProducts(),
                "Product should no longer be considered unpublished")

    @fixtures.fixture("Full")
    def testRemoveProductFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        project = client.getProject(data['projectId'])

        # sanity checks
        self.failUnless(data['pubProductId'] in pubRelease.getProducts(),
                "Product should be published before beginning")
        self.failIf(data['pubProductId'] in project.getUnpublishedProducts(),
                "Product should not be in the unpublished list")

        # unpublish it now
        pubRelease.removeProduct(data['pubProductId'])

        # check the state of the world after publishing
        self.failIf(data['productId'] in pubRelease.getProducts(),
                "Product was not removed from published releases")
        self.failUnless(data['productId'] in project.getUnpublishedProducts(),
                "Product should be considered unpublished")

    @fixtures.fixture("Full")
    def testUpdatePublishedRelease(self, db, data):

        releaseName = "My new release"
        releaseDescription = "My pithy description"

        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        # set some things
        pubRelease.name = releaseName
        pubRelease.description = releaseDescription
        self.failUnless(pubRelease.name == releaseName)
        self.failUnless(pubRelease.description == releaseDescription)
        self.failIf(pubRelease.timeUpdated, "timeUpdated should not be set")
        self.failIf(pubRelease.updatedBy, "updatedBy should not be set")

        # now save to the database
        pubRelease.save()

        # forget about it
        del pubRelease

        # retrieve it from the database, again
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        # check to make sure things are still set
        self.failUnless(pubRelease.name == releaseName)
        self.failUnless(pubRelease.description == releaseDescription)

        # check update fields
        self.failUnless(pubRelease.timeUpdated > 0, "timeUpdated not set")
        self.failUnless(pubRelease.updatedBy == data['owner'], "updatedBy should be set, now")

    @fixtures.fixture("Full")
    def testIsProductPublished(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        pubProduct = client.getProduct(data['pubProductId'])

        self.failIf(product.getPublished(), "Release should be published")
        self.failUnless(pubProduct.getPublished(), "Release should not be published")

    @fixtures.fixture("Full")
    def testGetPublishedReleasesByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getPublishedReleases(), [ data['pubReleaseId'] ])

    @fixtures.fixture("Full")
    def testGetUnpublishedProductsByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getUnpublishedProducts(), [ data['productId'] ])

    @fixtures.fixture("Full")
    def testDeletePublishedRelease(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        client.deletePublishedRelease(data['pubReleaseId'])

        self.failUnlessEqual(project.getPublishedReleases(), [],
                "There should be no published releases in the project")

        self.failUnless(data['pubProductId'] in project.getUnpublishedProducts(),
                "Previously published products should now be unpublished")

        product = client.getProduct(data['pubProductId'])

        self.failIf(product.getPublished(), "Product still shows up as published")

    @fixtures.fixture("Full")
    def testFinalizePublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])

        self.failIf(pubRelease.timePublished,
                "Release should not be published yet")
        self.failIf(pubRelease.publishedBy,
                "Release should not be published yet")

        pubRelease.finalize()
        pubRelease.refresh()

        self.assertAlmostEqual(pubRelease.timePublished, time.time(), 1,
                "Release should be published now")
        self.failUnlessEqual(pubRelease.publishedBy, data['owner'],
                "Release wasn't marked with the appropriate publisher")
        self.failUnless(pubRelease.isFinalized())

    @fixtures.fixture("Full")
    def testPublishEmptyProduct(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        self.assertRaises(ProductEmpty,
                pubRelease.addProduct, data['productId'])

    @fixtures.fixture("Full")
    def testDeleteProductFromPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubProduct = client.getProduct(data['pubProductId'])
        pubProduct.deleteProduct()

    @fixtures.fixture("Full")
    def testDeleteProductFromFinalizedPublishedRelease(self, db, data):
        client = self.getClient("owner")
        pubProduct = client.getProduct(data['pubProductId'])
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        pubRelease.finalize()
        self.assertRaises(ProductPublished, pubProduct.deleteProduct)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreate(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = client.newPublishedRelease(data['projectId'])
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, data['projectId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreateInHidden(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, PermissionDenied) }

        # make a project hidden
        adminClient = self.getClient("admin")
        adminClient.hideProject(data['projectId'])

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = client.newPublishedRelease(data['projectId'])
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, data['projectId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessGetNonPublic(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (True, None),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, ItemNotFound) }

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                pubRelease = client.getPublishedRelease(data['pubReleaseId'])
                self.failUnlessEqual(pubRelease.id, data['pubReleaseId'])
            else:
                self.assertRaises(exc,
                        client.getPublishedRelease, data['pubReleaseId'])

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessGetPublic(self, db, data):

        # this function should allow all users
        users = [ "admin", "owner", "developer",
                  "user", "nobody", "anonymous"]

        for user in users:
            # finalize the release before testing
            adminClient = self.getClient("admin")
            newProduct = adminClient.newProduct(data['projectId'],
                    "Test Published Product")
            newProduct.setProductType(producttypes.STUB_IMAGE)
            newProduct.setFiles([["file", "file title 1"]])
            newProduct.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newPubRelease.addProduct(newProduct.id)
            newPubRelease.finalize()

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)
            self.failUnlessEqual(newPubRelease.id, userPubRelease.id)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessCreateWithinOtherProject(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (False, PermissionDenied),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied)}

        # create an unrelated project using a seperate admin client
        adminClient = self.getClient("admin")
        otherProjectId = adminClient.newProject('Quux', 'quux', 'rpath.org')

        for (user, (allowed, exc)) in acls.items():
            client = self.getClient(user)

            if allowed:
                newPublishedRelease = \
                    client.newPublishedRelease(otherProjectId)
                self.failUnlessEqual(newPublishedRelease.createdBy,
                        data[user])
            else:
                self.assertRaises(exc,
                        client.newPublishedRelease, otherProjectId)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessAddProduct(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newProduct = adminClient.newProduct(data['projectId'],
                    "Test Published Product")
            newProduct.setProductType(producttypes.STUB_IMAGE)
            newProduct.setFiles([["file", "file title 1"]])
            newProduct.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                userPubRelease.addProduct(newProduct.id)
            else:
                self.assertRaises(exc,
                        userPubRelease.addProduct, newProduct.id)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessRemoveProduct(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newProduct = adminClient.newProduct(data['projectId'],
                    "Test Published Product")
            newProduct.setProductType(producttypes.STUB_IMAGE)
            newProduct.setFiles([["file", "file title 1"]])
            newProduct.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newPubRelease.addProduct(newProduct.id)

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                userPubRelease.removeProduct(newProduct.id)
            else:
                self.assertRaises(exc,
                        userPubRelease.removeProduct, newProduct.id)


    @fixtures.fixture("Full")
    def testPublishedReleaseAccessDelete(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, ItemNotFound),
                 'nobody': (False, ItemNotFound),
                 'anonymous': (False, PermissionDenied) }

        for (user, (allowed, exc)) in acls.items():

            adminClient = self.getClient("admin")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])

            client = self.getClient(user)

            if allowed:
                client.deletePublishedRelease(newPubRelease.id)
            else:
                self.assertRaises(exc,
                        client.deletePublishedRelease, newPubRelease.id)

    @fixtures.fixture("Full")
    def testPublishedReleaseAccessDeleteFinalized(self, db, data):
        acls = { 'admin': (True, None),
                 'owner': (True, None),
                 'developer': (False, PermissionDenied),
                 'user': (False, PermissionDenied),
                 'nobody': (False, PermissionDenied),
                 'anonymous': (False, PermissionDenied)}

        for (user, (allowed, exc)) in acls.items():
            adminClient = self.getClient("admin")
            newPubRelease = adminClient.newPublishedRelease(data['projectId'])
            newProduct = adminClient.newProduct(data['projectId'],
                    "Test Published Product")
            newProduct.setProductType(producttypes.STUB_IMAGE)
            newProduct.setFiles([["file", "file title 1"]])
            newProduct.setTrove("group-dist", "/testproject." + \
                    MINT_PROJECT_DOMAIN + "@rpl:devel/1.0-2-1", "1#x86")
            newPubRelease.addProduct(newProduct.id)
            newPubRelease.finalize()

            client = self.getClient(user)
            userPubRelease = client.getPublishedRelease(newPubRelease.id)

            if allowed:
                client.deletePublishedRelease(newPubRelease.id)
            else:
                self.assertRaises(exc,
                        client.deletePublishedRelease, newPubRelease.id)


    # XXX this probably needs to be getPublishedReleases, now
    # TODO rework me completely
    @fixtures.fixture("Full")
    def testPublishedReleasesList(self, db, data):
        #client, userId = self.quickMintUser("testuser", "testpass")
        #adminClient, adminuserId = self.quickMintAdmin("adminauth", "adminpass")
        raise testsuite.SkipTestException

        client = self.getClient("owner")
        adminClient = self.getClient("admin")
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
                pubRelease = client.newPublishedRelease()
                pubRelease.addProduct(product.id)
                pubRelease.save()
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


if __name__ == "__main__":
    testsuite.main()

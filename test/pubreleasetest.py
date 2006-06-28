#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()

import fixtures
from mint import producttypes
from mint import pubreleases

class PublishedReleaseTest(fixtures.FixturedUnitTest):

    @fixtures.fixture("Full")
    def testReleaseCreation(self, db, data):

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
    def testAddProductToRelease(self, db, data):

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
    def testRemoveProductFromRelease(self, db, data):
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
    def testUpdateRelease(self, db, data):

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
    def testProductPublishedState(self, db, data):
        client = self.getClient("owner")
        product = client.getProduct(data['productId'])
        pubProduct = client.getProduct(data['pubProductId'])

        self.failIf(product.getPublished(), "Release should be published")
        self.failUnless(pubProduct.getPublished(), "Release should not be published")

    @fixtures.fixture("Full")
    def testGetReleasesByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getPublishedReleases(), [ data['pubReleaseId'] ])

    @fixtures.fixture("Full")
    def testGetUnpublishedReleasesByProject(self, db, data):
        client = self.getClient("owner")
        project = client.getProject(data['projectId'])
        self.failUnlessEqual(project.getUnpublishedProducts(), [ data['productId'] ])

    @fixtures.fixture("Full")
    def testDeleteRelease(self, db, data):
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
    def testReleaseVisibility(self, db, data):
        client = self.getClient("owner")
        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        self.failUnlessEqual(pubRelease.visibility,
                pubreleases.VISIBILITY_PROJECT_ONLY,
                "This release should default to project-only visibility")

        pubRelease.visibility = pubreleases.VISIBILITY_PUBLIC
        pubRelease.save()

        del pubRelease

        pubRelease = client.getPublishedRelease(data['pubReleaseId'])
        self.failUnless(pubRelease.isPublicallyVisible(),
                "This release should be publically visible")

if __name__ == "__main__":
    testsuite.main()

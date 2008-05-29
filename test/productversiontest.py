#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#
import StringIO

import testsuite
testsuite.setup()

import fixtures
import mint_rephelp

from conary import conaryclient
from mint import mint_error
from mint import helperfuncs
from mint import userlevels
from mint_rephelp import MINT_PROJECT_DOMAIN

from rpath_common.proddef import api1 as proddef

class ProductVersionTest(fixtures.FixturedProductVersionTest):

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testAddProductVersion_Normal(self, db, data):
        """ Test adding a product version to the database. """
        projectId = data['projectId']
        ownerClient = self.getClient('owner')
        versionId = ownerClient.addProductVersion(projectId, '1',
                                                  description='Version 1')
        versionDict = ownerClient.getProductVersion(versionId)
        self.failUnlessEqual('1', versionDict['name'],
                             'Name did not get set properly')
        self.failUnlessEqual('Version 1', versionDict['description'],
                             'Description did not get set properly')
        
    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testAddProductVersion_NoDesc(self, db, data):
        """ Test adding a product version with no description. """
        projectId = data['projectId']
        ownerClient = self.getClient('owner')
        versionId = ownerClient.addProductVersion(projectId, '1')
        versionDict = ownerClient.getProductVersion(versionId)
        self.failIf(versionDict['description'], "Description should be blank")
         
    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testAddDuplicateProductVersion(self, db, data):
        """ Test attempting to add the same version twice. This should
            raise DuplicateProductVersion """
        projectId = data['projectId']
        ownerClient = self.getClient('owner')
        versionId = ownerClient.addProductVersion(projectId, '1')
        
        self.failUnlessRaises(mint_error.DuplicateProductVersion,
                              ownerClient.addProductVersion,
                              projectId, '1')
        
    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetProductVersion(self, db, data):
        ownerClient = self.getClient('owner')

        versionId = data['versionId']
        versionDict = ownerClient.getProductVersion(versionId)
        self.assertEquals('FooV1', versionDict['name'])
        self.assertEquals('FooV1Description', versionDict['description'])

        versionId2 = data['versionId2']
        versionDict2 = ownerClient.getProductVersion(versionId2)
        self.assertEquals('FooV2', versionDict2['name'])
        self.assertEquals('FooV2Description', versionDict2['description'])

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetNonExistantProductVersion(self, db, data):
        ownerClient = self.getClient('owner')
        # Let's hope there isn't really a version with this id.
        versionId = 1234567890
        self.assertRaises(mint_error.ProductVersionNotFound,
                          ownerClient.getProductVersion, versionId)
        

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testEditProductVersion(self, db, data):
        ownerClient = self.getClient('owner')
        versionId = data['versionId']
        newDesc = 'Description from unit tests'
        editVersionBool = ownerClient.editProductVersion(versionId, newDesc)
        self.assertEquals(True, editVersionBool)

        # Fetch the product version back out and verify it has the newly set
        # description.
        versionDict = ownerClient.getProductVersion(versionId)
        self.assertEquals(newDesc, versionDict['description'])

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testAccessDenied(self, db, data):
        """ Make sure that only admins and owners can add a
            product version. """
        projectId = data['projectId']
        
        # these should fail
        for username in ('nobody', 'developer', 'user'):
            c = self.getClient(username)
            self.failUnlessRaises(mint_error.PermissionDenied,
                                  c.addProductVersion, projectId,
                                  '1_%s' % username)
        
        # these should work
        for username in ('admin', 'owner'):
            c = self.getClient(username)
            self.failUnless(c.addProductVersion,
                            "This should have worked for %s" % username)
        
    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetProductVersionListForProduct(self, db, data):
        ownerClient = self.getClient('owner')
        projectId = data['projectId']
        productVersions = ownerClient.getProductVersionListForProduct(projectId)

        # There should be 2 versions.
        self.assertEquals(2, len(productVersions))

        names = ['FooV1', 'FooV2']
        descriptions = ['FooV1Description', 'FooV2Description']

        for pv in productVersions:
            names.pop(names.index(pv[2]))
            descriptions.pop(descriptions.index(pv[3]))

        self.assertEquals(0, len(names))
        self.assertEquals(0, len(descriptions))

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetProductVersionListForNonExistantProduct(self, db, data):
        ownerClient = self.getClient('owner')
        # Let's hope there isn't really a project with this id.
        projectId = 1234567890
        productVersions = ownerClient.getProductVersionListForProduct(projectId)

        # There should be 0 versions.
        self.assertEquals(0, len(productVersions))

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetandSetProductDefinitionForVersion(self, db, data):
        ownerClient = self.getClient('owner')
        versionId = data['versionId']

        pd = proddef.ProductDefinition()
        pd.addStage('devel', '-devel')
        pd.addStage('qa', '-qa')
        pd.addStage('release', '')

        ownerClient.setProductDefinitionForVersion(versionId, pd)
        npd = ownerClient.getProductDefinitionForVersion(versionId)

        self.failUnlessEqual(npd.getStage('devel').name, 'devel')
        self.failUnlessEqual(npd.getStage('devel').labelSuffix, '-devel')
        self.failUnlessEqual(npd.getStage('qa').name, 'qa')
        self.failUnlessEqual(npd.getStage('qa').labelSuffix, '-qa')
        self.failUnlessEqual(npd.getStage('release').name, 'release')
        self.failUnlessEqual(npd.getStage('release').labelSuffix, '')

    @testsuite.context('more_cowbell')
    @fixtures.fixture("Full")
    def testGetProductDefinitionForNonExistantVersion(self, db, data):
        ownerClient = self.getClient('owner')
        versionId = data['versionId']

        self.assertRaises(mint_error.ProductDefinitionVersionNotFound,
                              ownerClient.getProductDefinitionForVersion,
                              versionId)

class ProjectVersionWebTest(mint_rephelp.WebRepositoryHelper):

    def testProductVersionCreateNewNotOwner(self):
        """
        Must be owner to create new product version
        """
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject/editVersion',
                                      server=self.getProjectServerHostname())
        assert 'permission denied' in page.body.lower()

    def testProductVersionCreateNew(self):
        """
        Ensure owner can create product version
        """
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.addMemberById(userId, userlevels.OWNER)
        self.webLogin('testuser', 'testpass')

        page = self.fetchWithRedirect('/project/testproject/editVersion',
                                      server=self.getProjectServerHostname())
        assert 'create new %s version'%pText in page.body.lower()

    def testProductVersionEditNotOwner(self):
        """
        Must be owner to edit product version
        """
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        # add product version
        versionId = client.addProductVersion(projectId, 'foo', 'foo version')

        page = self.fetchWithRedirect(
            '/project/testproject/editVersion?id=%d'%versionId,
            server=self.getProjectServerHostname())
        assert 'permission denied' in page.body.lower()

    def testProductVersionEdit(self):
        """
        Ensure owner can edit a product version
        """
        raise testsuite.SkipTestException("This test has been skipped and needs some love.  It hangs forever on the postForm (RBL-2823)")
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.addMemberById(userId, userlevels.OWNER)
        self.webLogin('testuser', 'testpass')

        # add product version
        versionId = client.addProductVersion(projectId, 'foo', 'foo version')

        page = self.fetchWithRedirect(
           '/project/testproject/editVersion?id=%d'%versionId,
           server=self.getProjectServerHostname())
        assert 'edit %s version'%pText in page.body.lower()

    def testProductVersionEditLinkedNotOwner(self):
        """
        Must be owner to edit product version linked to creating product
        """
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        # add product version
        versionId = client.addProductVersion(projectId, 'foo', 'foo version')

        page = self.fetchWithRedirect(
            '/project/testproject/editVersion?id=%d?linked=true'%versionId,
            server=self.getProjectServerHostname())
        assert 'permission denied' in page.body.lower()


    def testProductVersionEditLinked(self):
        """
        Ensure owner can edit a product version linked to creating a product
        """
        raise testsuite.SkipTestException("This test has been skipped and needs some love.  It hangs forever on the postForm (RBL-2823)")
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.addMemberById(userId, userlevels.OWNER)
        self.webLogin('testuser', 'testpass')

        # add product version
        versionId = client.addProductVersion(projectId, 'foo', 'foo version')

        page = self.fetchWithRedirect(
           '/project/testproject/editVersion?id=%d&linked=true'%versionId,
           server=self.getProjectServerHostname())
        assert 'update initial %s version'%pText in page.body.lower()


if __name__ == "__main__":
    testsuite.main()


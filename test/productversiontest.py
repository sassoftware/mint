#!/usr/bin/python2.4
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import fixtures

from mint import mint_error

class ProductVersionTest(fixtures.FixturedUnitTest):
    
#    def addProductVersion(self, projectId, name, description=''):
#        return self.server.addProductVersion(projectId, name, description)
#
#    def getProductVersion(self, versionId):
#        return self.server.getProductVersion(versionId)
#
#    def getProductDefinitionForVersion(self, versionId):
#        return self.server.getProductDefinitionForVersion(versionId)
#
#    def setProductDefinitionForVersion(self, versionId, productDefinitionDict):
#        return self.server.setProductDefinitionForVersion(versionId,
#                productDefinitionDict)
#
#    def editProductVersion(self, versionId, newDesc):
#        return self.server.editProductVersion(versionId, newDesc)
#
#    def getProductVersionList(self):
#        return self.server.getProductVersionList()
    
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
        
    @fixtures.fixture("Full")
    def testAddProductVersion_NoDesc(self, db, data):
        """ Test adding a product version with no description. """
        projectId = data['projectId']
        ownerClient = self.getClient('owner')
        versionId = ownerClient.addProductVersion(projectId, '1')
        versionDict = ownerClient.getProductVersion(versionId)
        self.failIf(versionDict['description'], "Description should be blank")
         
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
        
    @fixtures.fixture("Full")
    def testUpdateVersion(self, db, data):
        raise testsuite.SkipTestException("Test needs to be implemented")

    @fixtures.fixture("Full")
    def testDeleteVersion(self, db, data):
        raise testsuite.SkipTestException("Test needs to be implemented")

    @fixtures.fixture("Full")
    def testFetchNonExistantVersion(self, db, data):
        raise testsuite.SkipTestException("Test needs to be implemented")
 
    @fixtures.fixture("Full")
    def testGetVersionListForProduct(self, db, data):
        raise testsuite.SkipTestException("Test needs to be implemented")
    
if __name__ == "__main__":
    testsuite.main()


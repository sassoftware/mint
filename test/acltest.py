#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
import testsuite
testsuite.setup()

import mint_rephelp

from mint import accesscontrol
from mint.accesscontrol import OBJ_TYPE_PROJECT, OBJ_TYPE_SITE, \
     ACTION_VIEW_PROJECT

# direct low level table manipulation functions
class AclTest(mint_rephelp.MintRepositoryHelper):
    def setUp(self):
        mint_rephelp.MintRepositoryHelper.setUp(self)
        self.permissions = accesscontrol.PermissionsTable(self.db)
        self.objects = accesscontrol.ObjectsTable(self.db)

        self.db.commit()

    def testDoubleGrant(self):
        # just want to be sure this doesn't trigger spurious errors
        self.permissions.grant(1, 1, 1)
        self.permissions.grant(1, 1, 1)

    def testRevokeNothing(self):
        # this behaves the same as a double revoke
        # just want to be sure this doesn't trigger spurious errors
        self.permissions.revoke(1, 1, 1)

    def testConflictingSite(self):
        self.objects.createObject(1, OBJ_TYPE_SITE)
        # expect a real error soon.
        self.assertRaises(AssertionError,
                          self.objects.createObject, 1, OBJ_TYPE_SITE)

    def testDirectPermission(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client, 'foo', 'Foo')
        self.objects.createObject(projectId, OBJ_TYPE_PROJECT)

        objectId = self.objects.getObjectId(projectId, OBJ_TYPE_PROJECT)

        groupId = client.server._server.userGroupMembers.getGroupsForUser( \
            userId)[0]
        self.permissions.grant(groupId, ACTION_VIEW_PROJECT, objectId)

        perm = self.permissions.getActionAllowed(userId, ACTION_VIEW_PROJECT,
                                          objectId)
        self.failIf(not perm, "Grant didn't invoke permission")
        self.permissions.revoke(groupId, ACTION_VIEW_PROJECT, objectId)
        perm = self.permissions.getActionAllowed(userId, ACTION_VIEW_PROJECT,
                                          objectId)
        self.failIf(perm, "Revoke didn't revoke permission")

    def testSitePermission(self):
        client, userId = self.quickMintUser('foouser', 'foopass')

        projectId = self.newProject(client, 'foo', 'Foo')

        self.objects.createObject(projectId, OBJ_TYPE_PROJECT)
        self.objects.createObject(0, OBJ_TYPE_SITE)

        objectId = self.objects.getObjectId(projectId, OBJ_TYPE_PROJECT)
        siteId = self.objects.getObjectId(0, OBJ_TYPE_SITE)

        groupId = client.server._server.userGroupMembers.getGroupsForUser( \
            userId)[0]
        self.permissions.grant(groupId, ACTION_VIEW_PROJECT, siteId)

        perm = self.permissions.getActionAllowed(userId, ACTION_VIEW_PROJECT,
                                          objectId)
        self.failIf(not perm, "Site-wide permission not inherited")
        self.permissions.revoke(groupId, ACTION_VIEW_PROJECT, siteId)
        perm = self.permissions.getActionAllowed(userId, ACTION_VIEW_PROJECT,
                                          objectId)
        self.failIf(perm, "Revoke didn't revoke permission")

    def testMissingSiteObject(self):
        client, userId = self.quickMintUser('foouser', 'foopass')

        projectId = self.newProject(client, 'foo', 'Foo')

        self.objects.createObject(projectId, OBJ_TYPE_PROJECT)

        objectId = self.objects.getObjectId(projectId, OBJ_TYPE_PROJECT)

        groupId = client.server._server.userGroupMembers.getGroupsForUser( \
            userId)[0]

        perm = self.permissions.getActionAllowed(userId, ACTION_VIEW_PROJECT,
                                                 objectId)
        self.failIf(perm, "Passed permission check illegally")

    def testPermissionOverlap(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client, 'foo', 'Foo')

        self.objects.createObject(projectId, OBJ_TYPE_PROJECT)
        #creat a permission with same ID pointer, but different
        self.objects.createObject(projectId, OBJ_TYPE_SITE)
        groupId = client.server._server.userGroupMembers.getGroupsForUser( \
            userId)[0]

        objectId = self.objects.getObjectId(projectId, OBJ_TYPE_PROJECT)
        siteObjId = self.objects.getObjectId(None, OBJ_TYPE_SITE)

        self.failIf(objectId == siteObjId,
                    "Objects Table did not distinguish Ids of differing type.")

if __name__ == '__main__':
    testsuite.main()

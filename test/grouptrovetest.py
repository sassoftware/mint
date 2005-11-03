#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
#

import testsuite
testsuite.setup()

from mint_rephelp import MintRepositoryHelper
from mint import mint_server
from repostest import testRecipe
import versions
from mint import grouptrove
from mint.database import ItemNotFound
from mint import userlevels
from mint.mint_error import PermissionDenied
from repository import netclient

refRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.add('testcase', 'test.localhost@rpl:devel', '', groupName = 'group-test')
"""


class GroupTroveTest(MintRepositoryHelper):
    def addTestTrove(self, groupTrove, trvName):
        trvVersion='/test.localhost@rpl:devel/1.0-1-1'
        trvFlavor='1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        return groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                   subGroup, False, False, False)

    def createTestGroupTrove(self, client, projectId):
        return client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                       'No Description', False)

    def testBasicAttributes(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)

        if not isinstance (groupTrove, grouptrove.GroupTrove):
            self.fail("createGroupTrove didn't return a GroupTrove object")
        groupTroveId = groupTrove.getId()

        client.createGroupTrove(projectId, 'group-test2', '1.0.1',
                                'some sort of description', False)
        gtList = client.listGroupTrovesByProject(projectId)
        refGtList = [(1, 'group-test'), (2, 'group-test2')]
        if gtList != refGtList:
            self.fail("listGroupTrovesByProject returned the wrong results: got %s but expected %s"% (str(gtList), str(refGtList)))

        groupTrove.delete()
        try:
            client.getGroupTrove(groupTroveId)
            self.fail("getGroupTrove should have failed for nonexistent trove")
        except ItemNotFound:
            pass

    def testVersionLock(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, 'testcase')

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is False)

        assert(gTrv['trvVersion'] == 'test.localhost@rpl:devel')

        groupTrove.setTroveVersionLocked(trvId, True)

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is True)

        assert(gTrv['trvVersion'] == '/test.localhost@rpl:devel/1.0-1-1')

    def testAutoResolve(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        assert(groupTrove.autoResolve is False)

        groupTrove.setAutoResolve(True)
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.autoResolve is True)

        groupTrove.setAutoResolve(False)
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.autoResolve is False)

    def testFlavorLock(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, 'testcase')
        gTrv = groupTrove.getTrove(trvId)

        assert(gTrv['trvFlavor'] == '')

        assert(gTrv['useLock'] is False)
        assert(gTrv['instSetLock'] is False)
        groupTrove.setTroveUseLocked(trvId, True)
        gTrv = groupTrove.getTrove(trvId)

        assert(gTrv['useLock'] is True)
        assert(gTrv['trvFlavor'] == '~!kernel.debug,~kernel.smp')

        groupTrove.setTroveInstSetLocked(trvId, True)
        gTrv = groupTrove.getTrove(trvId)

        assert(gTrv['instSetLock'] is True)
        assert(gTrv['trvFlavor'] == '~!kernel.debug,~kernel.smp is: x86')

        groupTrove.setTroveUseLocked(trvId, False)
        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['trvFlavor'] == 'is: x86')


    def testListGroupTroveItems(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")
        trv2Id = self.addTestTrove(groupTrove, "testcase2")

        if len(groupTrove.listTroves()) != 2:
            self.fail("listTroves returned the wrong number of results, we expected two.")

        groupTrove.delTrove(trv2Id)

        if len(groupTrove.listTroves()) != 1:
            self.fail("groupTrove.delTrove didn't work.")

    def testGroupTroveDesc(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")

        desc = 'A different description'

        groupTrove.setDesc(desc)

        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.description == desc)

    def testSubGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['subGroup'] == 'group-test')

        groupTrove.setTroveSubGroup(trvId, "group-foo")
        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['subGroup'] == 'group-foo')

    def testUpstreamVersion(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")

        gTrv = groupTrove.getTrove(trvId)
        assert(groupTrove.upstreamVersion == '1.0.0')

        groupTrove.setUpstreamVersion("1.0.1")
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.upstreamVersion == '1.0.1')

    def testBadParams(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)
        try:
            client.createGroupTrove(projectId, 'group!test', '1.0.0',
                                    'No Description', False)
            self.fail("Group Trove with bad name was allowed")
        except grouptrove.GroupTroveNameError:
            pass

        try:
            client.createGroupTrove(projectId, 'group-test', '1-0.0',
                                    'No Description', False)
            self.fail("Group Trove with version name was allowed (create)")
        except grouptrove.GroupTroveVersionError:
            pass

        groupTrove = self.createTestGroupTrove(client, projectId)

        try:
            groupTrove.setUpstreamVersion('1-0.0')
            self.fail("Group Trove with bad version was allowed (modify)")
        except grouptrove.GroupTroveVersionError:
            pass

    def testPermissions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        adminClient, adminId = self.quickMintAdmin('adminuser','testpass')
        projectId = self.newProject(adminClient)
        project = adminClient.getProject(projectId)
        adminClient.hideProject(projectId)
        groupTrove = self.createTestGroupTrove(adminClient, projectId)
        groupTroveId = groupTrove.getId()
        trvId = self.addTestTrove(groupTrove, 'testtrove')


        try:
            client.server.getGroupTrove(groupTroveId)
            self.fail("groupTrove of hidden project visible to nonmembers")
        except ItemNotFound:
            pass

        try:
            client.server.delGroupTroveItem(trvId)
            self.fail("groupTroveItems of hidden project visible to nonmembers")
        except ItemNotFound:
            pass


        project.addMemberById(userId, userlevels.DEVELOPER)
        try:
            client.server.getGroupTrove(groupTroveId)
            self.fail("non-owner allowed to manipuate group trove")
        except PermissionDenied:
            pass

        try:
            client.server.delGroupTroveItem(trvId)
            self.fail("non-owner allowed to maniplaute group trove item")
        except PermissionDenied:
            pass

        project.addMemberById(userId, userlevels.OWNER)
        client.server.getGroupTrove(groupTroveId)
        client.server.delGroupTroveItem(trvId)

    def testGetRecipe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")

        if (groupTrove.getRecipe() != refRecipe):
            self.fail("auto generated recipe did not return expected results")

    def testCookAutoRecipe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.localhost@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")

        self.makeSourceTrove("group-test", groupTrove.getRecipe())
        self.cookFromRepository("group-test",
            versions.Label("test.localhost@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)

        troveNames = nc.troveNames(versions.Label("test.localhost@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'test.localhost@rpl:devel': ['group-test']})

    def testCookOnServer(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.localhost@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")
        groupTrove.cook()

        cfg = project.getConaryConfig()
        nc = netclient.NetworkRepositoryClient(cfg.repositoryMap)

        # FIXME: cook twice in a row and actually verify version numbers

        troveNames = nc.troveNames(versions.Label("test.localhost@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'test.localhost@rpl:devel': ['group-test']})

if __name__ == "__main__":
    testsuite.main()

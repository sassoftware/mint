#!/usr/bin/python2.4
#
# Copyright (c) 2004-2006 rPath, Inc.
#

import testsuite
testsuite.setup()
import os
import sys
import time

from conary import versions
from conary.conaryclient import ConaryClient

from repostest import testRecipe
from mint_rephelp import MintRepositoryHelper

from mint import jobstatus
from mint import mint_server
from mint import grouptrove
from mint import userlevels
from mint.database import ItemNotFound, DuplicateItem
from mint.mint_error import PermissionDenied
from mint.distro import group_trove
from mint.jobs import DuplicateJob

refRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.rpath.local@rpl:devel')
        r.add('testcase', 'testproject.rpath.local@rpl:devel', '', groupName = 'group-test')
"""

groupsRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.rpath.local@rpl:devel', 'conary.rpath.com@rpl:1')
        r.add('testcase', 'testproject.rpath.local@rpl:devel', '', groupName = 'group-test')
        if Arch.x86_64:
            r.add('group-core', 'conary.rpath.com@rpl:1', 'is:x86(i486,i586,i686) x86_64', groupName = 'group-test')
        else:
            r.add('group-core', 'conary.rpath.com@rpl:1', '', groupName = 'group-test')
"""

lockedRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.rpath.local@rpl:devel')
        r.add('testcase', '/testproject.rpath.local@rpl:devel/1.0-1-1', '', groupName = 'group-test')
"""

class GroupTroveTest(MintRepositoryHelper):
    def makeCookedTrove(self, branch = 'rpl:devel', hostname = 'testproject'):
        l = versions.Label("%s.rpath.local@%s" % (hostname, branch))
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l, ignoreDeps = True)

    def addTestTrove(self, groupTrove, trvName,
            trvVersion = '/testproject.rpath.local@rpl:devel/1.0-1-1',
            trvFlavor='1#x86|5#use:~!kernel.debug:~kernel.smp',
            subGroup = ''):
        return groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                   subGroup, False, False, False)

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
        self.failIf(gtList != refGtList,
                    "listGroupTrovesByProject returned the wrong results:"
                    " got %s but expected %s"% (str(gtList), str(refGtList)))

        groupTrove.delete()
        try:
            client.getGroupTrove(groupTroveId)
            self.fail("getGroupTrove should have failed for nonexistent trove")
        except ItemNotFound:
            pass

    def testUpstreamVersions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId,
                                               upstreamVer = '1.0')
        assert(groupTrove.upstreamVersion == '1.0')

        groupTrove.setUpstreamVersion('0.0')
        groupTrove.refresh()
        assert(groupTrove.upstreamVersion == '0.0')

        groupTrove.setUpstreamVersion('0')
        groupTrove.refresh()
        assert(groupTrove.upstreamVersion == '0')

        groupTrove.setUpstreamVersion('1')
        groupTrove.refresh()
        assert(groupTrove.upstreamVersion == '1')

        groupTrove.setUpstreamVersion('0.1.0')
        groupTrove.refresh()
        assert(groupTrove.upstreamVersion == '0.1.0')

    def testVersionLock(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, 'testcase')

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is False)

        assert(gTrv['trvVersion'] == '/testproject.rpath.local@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'testproject.rpath.local@rpl:devel')

        groupTrove.setTroveVersionLock(trvId, True)

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is True)

        assert(gTrv['trvVersion'] == '/testproject.rpath.local@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'testproject.rpath.local@rpl:devel')

    def testAddByProject(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        groupProjectId = self.newProject(client, name = 'Foo',
                                         hostname = 'foo')
        groupProject = client.getProject(groupProjectId)

        cu = self.db.cursor()
        cu.execute('UPDATE Labels SET label=? WHERE projectId=?',
                   'testproject.rpath.local@foo:bar', groupProjectId)
        self.db.commit()

        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, groupProjectId)
        groupTroveId = groupTrove.getId()

        # these branch names are not haphazard choices. order and exact
        # contents matter. each one is designed to override the previous.
        # other constructs may pass, but not consistently.
        # the first is utterly random
        # the second is the default project branch name from the target proejct
        # the third is the branch name of the project containing groupTrove
        for branch in ('ravenous:bugblatterbeast', 'rpl:devel', 'foo:bar'):
            refTrvVersion = '/testproject.rpath.local@%s/1.0-1-1' % branch

            self.makeCookedTrove(branch)

            trvId, trvName, trvVersion = \
                   groupTrove.addTroveByProject('testcase', 'testproject', '',
                                                '', False, False, False)

            if trvVersion != refTrvVersion:
                self.fail('Trove version was mangled. It is:\n%s, but it should have been:\n%s' %(trvVersion, refTrvVersion))

    def testAddPermissions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeCookedTrove('rpl:devel')

        newClient = self.openMintClient(('anonymous', 'anonymous'))
        # try with anonymous user
        # historically this raised a permission denied. with code stubs for
        # loginless group builder present this call will get two steps further
        # and trigger an ItemNotFound. The interface may be reverted in the
        # future.
        self.assertRaises(PermissionDenied,
                          newClient.server.addGroupTroveItemByProject,
                          groupTroveId, 'testcase', 'testproject', '', '',
                          False, False, False)

        newClient, newUserId = self.quickMintUser('anotherGuy','testpass')

        # try with non-member
        self.assertRaises(PermissionDenied,
                          newClient.server.addGroupTroveItemByProject,
                          groupTroveId, 'testcase', 'testproject', '', '',
                          False, False, False)

        # try with watcher
        userProject = newClient.getProject(projectId)
        userProject.addMemberById(newUserId, userlevels.USER)
        self.assertRaises(PermissionDenied,
                          newClient.server.addGroupTroveItemByProject,
                          groupTroveId, 'testcase', 'testproject', '', '',
                          False, False, False)

        # try with developer
        project.addMemberById(newUserId, userlevels.DEVELOPER)
        res = newClient.server.addGroupTroveItemByProject(groupTroveId,
                                                          'testcase',
                                                          'testproject',
                                                          '', '', False, False,
                                                          False)

        groupTrove.delTrove(res[0])

        # try with owner
        # we don't care about the output, just that there's no exception
        client.server.addGroupTroveItemByProject(groupTroveId, 'testcase',
                                                 'testproject', '', '', False,
                                                 False, False)

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
        groupTrove.setTroveUseLock(trvId, True)
        gTrv = groupTrove.getTrove(trvId)

        assert(gTrv['useLock'] is True)
        assert(gTrv['trvFlavor'] == '~!kernel.debug,~kernel.smp')

        groupTrove.setTroveInstSetLock(trvId, True)
        gTrv = groupTrove.getTrove(trvId)

        assert(gTrv['instSetLock'] is True)
        assert(gTrv['trvFlavor'] == '~!kernel.debug,~kernel.smp is: x86')

        groupTrove.setTroveUseLock(trvId, False)
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


        # manipulate items as developer
        project.addMemberById(userId, userlevels.DEVELOPER)
        client.server.getGroupTrove(groupTroveId)
        client.server.delGroupTroveItem(trvId)

        trvId = self.addTestTrove(groupTrove, 'testtrove')

        # manipulate items as owner
        project.addMemberById(userId, userlevels.OWNER)
        client.server.getGroupTrove(groupTroveId)
        client.server.delGroupTroveItem(trvId)

    def testGetRecipe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        trvId = self.addTestTrove(groupTrove, "testcase")
        assert(groupTrove.getRecipe() == refRecipe)

        groupTrove.setTroveVersionLock(trvId, True)
        assert(groupTrove.getRecipe() == lockedRecipe)
        groupTrove.setTroveVersionLock(trvId, False)

        # test the "fancy-flavored" group-core hack:
        groupTrove.addTrove('group-core', '/conary.rpath.com@rpl:devel//1/0.99.0-0.1-1',
            '1#x86:i486:i586:i686:~!sse2|1#x86_64|5#use:X:~!alternatives:~!bootstrap:'
            '~!builddocs:~buildtests:desktop:~!dietlibc:emacs:gcj:~glibc.tls:gnome:'
            '~grub.static:gtk:ipv6:kde:~!kernel.debug:~!kernel.debugdata:~!kernel.numa:'
            'krb:ldap:nptl:~!openssh.smartcard:~!openssh.static_libcrypto:pam:pcre:perl:'
            '~!pie:~!postfix.mysql:python:qt:readline:sasl:~!selinux:~sqlite.threadsafe:'
            'ssl:tcl:tcpwrappers:tk:~!xorg-x11.xprint', 'group-test', False, False, False)
        assert(groupTrove.getRecipe() == groupsRecipe)


    def testMultipleAdditions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.addTestTrove(groupTrove, "testcase")
        try:
            self.addTestTrove(groupTrove, "testcase")
        except DuplicateItem:
            pass
        else:
            self.fail("GroupTrove.addTrove allowed a duplicate entry."
                      "addTrove relies on a unique index,"
                      "please check that it's operative.")

    def testDuplicateLabels(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.addTestTrove(groupTrove, "testcase")
        self.addTestTrove(groupTrove, "testcase2")
        assert (groupTrove.getLabelPath() == ['testproject.rpath.local@rpl:devel'])

    @testsuite.context('broken')
    def testCookAutoRecipe(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject.rpath.local@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")

        self.makeSourceTrove("group-test", groupTrove.getRecipe())
        self.cookFromRepository("group-test",
            versions.Label("testproject.rpath.local@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject.rpath.local@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'testproject.rpath.local@rpl:devel': ['group-test']})

    def waitForCommit(self, project, troveList):
        iters = 0
        while True:
            time.sleep(0.1)
            iters += 1
            if [x[:2] for x in project.getCommits()] == troveList:
                break
            if iters > 50:
                self.fail("commits didn't show up")

    @testsuite.context('broken')
    def testCookOnServer(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject.rpath.local@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")
        # cook once to ensure we can create a new package
        jobId = groupTrove.startCookJob("1#x86")
        assert(jobId == groupTrove.getJob().id)
        job = client.getJob(jobId)
        try:
            groupTrove.startCookJob("1#x86")
            self.fail('groupTrove.cook() allowed conflicting cook job.')
        except DuplicateJob:
            pass

        isocfg = self.writeIsoGenCfg()
        cookJob = group_trove.GroupTroveCook(client, isocfg, job)
        trvName, trvVersion, trvFlavor = cookJob.write()

        # give some time for the commit action to run

        self.waitForCommit(project, [('group-test:source', '1.0.0-1'),
                                     ('testcase:source', '1.0-1')])

        job.setStatus(jobstatus.FINISHED,"Finished")
        # cook a second time to ensure we follow the checkout codepath
        # set the version lock while we're at it, to test the getRecipe path
        groupTrove.setTroveVersionLock(trvId, True)
        jobId = groupTrove.startCookJob("1#x86")
        job = client.getJob(jobId)
        assert(job.getDataValue("arch") == "1#x86")

        cookJob = group_trove.GroupTroveCook(client, isocfg, job)
        trvName, trvVersion, trvFlavor = cookJob.write()

        # give some time for the commit action to run
        self.waitForCommit(project, [('group-test:source', '1.0.0-2'),
                                     ('group-test:source', '1.0.0-1'),
                                     ('testcase:source', '1.0-1')])

        assert(trvName == 'group-test')
        assert(trvVersion == '/testproject.rpath.local@rpl:devel/1.0.0-2-1')
        assert(trvFlavor == '')

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label(
            "testproject.rpath.local@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'testproject.rpath.local@rpl:devel': ['group-test']})

    def addPackage(self, pkgName, v,
            components = ['devel', 'runtime'],
            filePrimers = {'devel': 0, 'runtime': 1}):
        l = []
        for c in components:
            self.addComponent(pkgName + ":" + c, v, filePrimer = filePrimers[c])
            l.append((pkgName + ":" + c, v))
        self.addCollection(pkgName, v, l)

    def testGroupTrovePathConflicts(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        v = versions.ThawVersion("/testproject.rpath.local@rpl:devel/123.0:1.0-1-1")
        v2 = versions.ThawVersion("/testproject.rpath.local@rpl:mumble/123.0:1.0-1-1")

        # trove1 on both v and v2, trove2 only on v2
        self.addPackage("trove1", v)
        self.addPackage("trove1", v2, filePrimers = {'devel': 2, 'runtime': 3})
        self.addPackage("trove2", v2)

        trvId = self.addTestTrove(groupTrove, "trove1", v.asString())
        trvId = self.addTestTrove(groupTrove, "trove2", v2.asString())
        # cook once to ensure we can create a new package
        jobId = groupTrove.startCookJob("1#x86")

        job = client.getJob(jobId)
        isocfg = self.writeIsoGenCfg()
        cookJob = group_trove.GroupTroveCook(client, isocfg, job)
        trvName, trvVersion, trvFlavor = cookJob.write()

        # give some time for the commit action to run
        self.waitForCommit(project, [('group-test:source', '1.0.0-2'),
                                     ('group-test:source', '1.0.0-1')])

        job.setStatus(jobstatus.FINISHED,"Finished")

    def testEmptyCook(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject.rpath.local@rpl:devel"), ignoreDeps = True)

        assert(len(groupTrove.listTroves()) == 0)

        try:
            groupTrove.startCookJob("1#x86")
        except mint_server.GroupTroveEmpty:
            pass
        else:
            self.fail("allowed to start an empty cook job")

        trvId = self.addTestTrove(groupTrove, "testcase")

        assert(len(groupTrove.listTroves()) == 1)

    def testSourceGroups(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)

        v = versions.ThawVersion( \
            "/testproject.rpath.local@rpl:devel/123.0:1.0-1-1")

        # should not be allowed to add source components to groups
        self.assertRaises(grouptrove.GroupTroveNameError, self.addTestTrove,
                          groupTrove, "test:source", v.asString())

if __name__ == "__main__":
    testsuite.main()

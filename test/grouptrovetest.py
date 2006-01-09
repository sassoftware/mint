#!/usr/bin/python2.4
#
# Copyright (c) 2004-2005 rPath, Inc.
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
        r.setLabelPath('test.rpath.local@rpl:devel')
        r.add('testcase', 'test.rpath.local@rpl:devel', '', groupName = 'group-test')
"""

groupsRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('test.rpath.local@rpl:devel', 'conary.rpath.com@rpl:1')
        r.add('testcase', 'test.rpath.local@rpl:devel', '', groupName = 'group-test')
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
        r.setLabelPath('test.rpath.local@rpl:devel')
        r.add('testcase', '/test.rpath.local@rpl:devel/1.0-1-1', '', groupName = 'group-test')
"""

class GroupTroveTest(MintRepositoryHelper):
    def makeCookedTrove(self, branch):
        l = versions.Label("test.rpath.local@%s" % branch)
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l, ignoreDeps = True)

    def addTestTrove(self, groupTrove, trvName):
        trvVersion='/test.rpath.local@rpl:devel/1.0-1-1'
        trvFlavor='1#x86|5#use:~!kernel.debug:~kernel.smp'
        subGroup = ''

        return groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                                   subGroup, False, False, False)

    def createTestGroupTrove(self, client, projectId,
        name = 'group-test', upstreamVer = '1.0.0',
        description = 'No Description'):
        return client.createGroupTrove(projectId, name, upstreamVer, description, False)

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

    @testsuite.context('loginless')
    def testTransGrpTrvCleanup(self):
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        cu = self.db.cursor()
        cu.execute("UPDATE GroupTroves SET timeModified=?",
                   time.time() - 86300)
        self.db.commit()

        client.server.cleanupGroupTroves()

        # cleanup should not have deleted item.
        client.getGroupTrove(groupTrove.id)

        cu.execute("UPDATE GroupTroves SET timeModified=?",
                   time.time() - 86401)
        self.db.commit()

        client.server.cleanupGroupTroves()

        self.assertRaises(ItemNotFound, client.getGroupTrove, groupTrove.id)

    @testsuite.context('loginless')
    def testTransGrpTrvProject(self):
        client, userId = self.quickMintUser('foo', 'bar')
        projectId = self.newProject(client)

        # forget client
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        # there's not actually a project, so listing can't work.
        self.assertRaises(PermissionDenied, client.listGroupTrovesByProject, 0)

    @testsuite.context('loginless')
    def testTransGrpTrvAdd(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        self.makeCookedTrove('foo:bar')

        # forget client
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        groupTrove.addTroveByProject('testcase', 'test', '', '', False, False,
                                     False)

    @testsuite.context('loginless')
    def testTransGrpTrvList(self):
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        self.failIf(groupTrove.listTroves() != [],
                    "Listing items of transient group trove failed.")

    @testsuite.context('loginless')
    def testTransGrpTrvDesc(self):
        client = self.openMintClient()

        groupTrove = self.createTestGroupTrove(client, 0)

        groupTrove.setDesc('What do you mean? African or European?')

    @testsuite.context('loginless')
    def testTransGrpTrvVersionLock(self):
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        trvId = self.addTestTrove(groupTrove, 'testcase')

        groupTrove.setTroveVersionLock(trvId, True)

    @testsuite.context('loginless')
    def testTransGrpTrvUseLock(self):
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        trvId = self.addTestTrove(groupTrove, 'testcase')

        groupTrove.setTroveUseLock(trvId, True)

    @testsuite.context('loginless')
    def testTransGrpTrvInstSetLock(self):
        client = self.openMintClient()
        groupTrove = self.createTestGroupTrove(client, 0)

        trvId = self.addTestTrove(groupTrove, 'testcase')

        groupTrove.setTroveInstSetLock(trvId, True)

    @testsuite.context('loginless')
    def testTransGrpTrvVersion(self):
        client = self.openMintClient()

        groupTrove = self.createTestGroupTrove(client, 0)
        groupTroveId = groupTrove.getId()

        assert(groupTrove.upstreamVersion == '1.0.0')

        groupTrove.setUpstreamVersion("1.0.1")
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.upstreamVersion == '1.0.1')

    @testsuite.context('loginless')
    def testTransGrpTrvRecipe(self):
        client = self.openMintClient()
        groupTrove= self.createTestGroupTrove(client, 0)

        trvId = self.addTestTrove(groupTrove, "testcase")

        groupTrove.getRecipe()

    @testsuite.context('loginless')
    def testTransGrpTrvCook(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        #forget the client
        client = self.openMintClient()

        groupTrove = self.createTestGroupTrove(client, 0)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")
        # cook once to ensure we can create a new package
        jobId = groupTrove.startCookJob("1#x86")
        job = client.getJob(jobId)

        cookJob = group_trove.GroupTroveCook(client, client.getCfg(), job,
                                             groupTrove.getId())

        # nasty hack. gencslist currently dumps to stderr...
        # fd's routed to /dev/null to clean up output
        oldFd = os.dup(sys.stderr.fileno())
        fd = os.open(os.devnull, os.W_OK)
        os.dup2(fd, sys.stderr.fileno())
        os.close(fd)
        try:
            assert(cookJob.write() is not None)
        finally:
            #recover old fd
            os.dup2(oldFd, sys.stderr.fileno())
            os.close(oldFd)

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

        assert(gTrv['trvVersion'] == '/test.rpath.local@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'test.rpath.local@rpl:devel')

        groupTrove.setTroveVersionLock(trvId, True)

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is True)

        assert(gTrv['trvVersion'] == '/test.rpath.local@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'test.rpath.local@rpl:devel')

    def testAddByProject(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        groupProjectId = self.newProject(client, name = 'Foo',
                                         hostname = 'foo')
        groupProject = client.getProject(groupProjectId)

        cu = self.db.cursor()
        cu.execute('UPDATE Labels SET label=? WHERE projectId=?',
                   'test.rpath.local@foo:bar', groupProjectId)
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
            refTrvVersion = '/test.rpath.local@%s/1.0-1-1' % branch

            self.makeCookedTrove(branch)

            trvId, trvName, trvVersion = \
                   groupTrove.addTroveByProject('testcase', 'test', '', '',
                                                False, False, False)

            if trvVersion != refTrvVersion:
                self.fail('Trove version was mangled. It is:\n%s, but it should have been:\n%s' %(trvVersion, refTrvVersion))

    def testAddPermissions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()
        newClient = self.openMintClient(('anonymous', 'anonymous'))
        try:
            newClient.server.addGroupTroveItemByProject(groupTroveId,
                                                        'testcase', 'test', '',
                                                        '', False, False,
                                                        False)
        except PermissionDenied:
            pass
        else:
            self.fail('Anonymous user allowed to add group trove item')

        newClient, garbage = self.quickMintUser('anotherGuy','testpass')
        try:
            newClient.server.addGroupTroveItemByProject(groupTroveId,
                                                        'testcase', 'test', '',
                                                        '', False, False,
                                                        False)
        except PermissionDenied:
            pass
        else:
            self.fail('Non-member user allowed to add group trove item')

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
        assert (groupTrove.getLabelPath() == ['test.rpath.local@rpl:devel'])

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
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        trvId = self.addTestTrove(groupTrove, "testcase")

        self.makeSourceTrove("group-test", groupTrove.getRecipe())
        self.cookFromRepository("group-test",
            versions.Label("test.rpath.local@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("test.rpath.local@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'test.rpath.local@rpl:devel': ['group-test']})

    def waitForCommit(self, project, troveList):
        iters = 0
        while True:
            time.sleep(0.1)
            iters += 1
            if project.getCommits() == troveList:
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
            versions.Label("test.rpath.local@rpl:devel"),
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

        cookJob = group_trove.GroupTroveCook(client, client.getCfg(), job,
                                             groupTrove.id)
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

        cookJob = group_trove.GroupTroveCook(client, client.getCfg(), job,
                                             groupTrove.getId())
        trvName, trvVersion, trvFlavor = cookJob.write()

        # give some time for the commit action to run
        self.waitForCommit(project, [('group-test:source', '1.0.0-2'),
                                     ('group-test:source', '1.0.0-1'),
                                     ('testcase:source', '1.0-1')])

        assert(trvName == 'group-test')
        assert(trvVersion == '/test.rpath.local@rpl:devel/1.0.0-2-1')
        assert(trvFlavor == '')

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label(
            "test.rpath.local@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == {'test.rpath.local@rpl:devel': ['group-test']})

    def testEmptyCook(self):
        self.openRepository()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"), ignoreDeps = True)

        assert(len(groupTrove.listTroves()) == 0)

        try:
            groupTrove.startCookJob("1#x86")
        except mint_server.GroupTroveEmpty:
            pass
        else:
            self.fail("allowed to start an empty cook job")

        trvId = self.addTestTrove(groupTrove, "testcase")

        assert(len(groupTrove.listTroves()) == 1)

if __name__ == "__main__":
    testsuite.main()

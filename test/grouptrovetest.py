#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import testsuite
testsuite.setup()
import os
import sys
import time

import simplejson

from conary import versions
from conary.deps import deps
from conary.conaryclient import ConaryClient

import fixtures
from repostest import testRecipe
from mint_rephelp import MintRepositoryHelper
from mint_rephelp import MINT_PROJECT_DOMAIN

from mint import jobstatus
from mint import grouptrove
from mint import server
from mint import userlevels
from mint.database import ItemNotFound, DuplicateItem
from mint.mint_error import PermissionDenied, ParameterError
from mint.distro import group_trove
from mint.jobs import DuplicateJob

refRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.%s@rpl:devel')
        r.add('testcase', 'testproject.%s@rpl:devel', '', groupName = 'group-test')
""" % ((MINT_PROJECT_DOMAIN,) * 2)

refCompRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('foo.%s@rpl:devel')
        r.removeComponents(('devel', 'doc'))
""" % (MINT_PROJECT_DOMAIN)

groupsRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.%s@rpl:devel', 'conary.rpath.com@rpl:1')
        r.add('testcase', 'testproject.%s@rpl:devel', '', groupName = 'group-test')
        if Arch.x86_64:
            r.add('group-core', flavor = 'is:x86(i486,i586,i686) x86_64', groupName = 'group-test', searchPath = ['addons.rpath.com@rpl:1', 'conary.rpath.com@rpl:1'])
        else:
            r.add('group-core', flavor = 'is: x86', groupName = 'group-test', searchPath = ['addons.rpath.com@rpl:1', 'conary.rpath.com@rpl:1'])
""" % ((MINT_PROJECT_DOMAIN,) * 2)

refRedirRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.%s@rpl:devel')
        r.add('testcase', 'testproject.%s@rpl:devel', '', groupName = 'group-test')
        r.add('redirect:lib', 'testproject.%s@rpl:devel', '', groupName = 'group-test')
        if Arch.x86:
            r.add('test:lib', '/testproject.%s@rpl:devel/1.0-1-1', 'is: x86', groupName = 'group-test')
""" % ((MINT_PROJECT_DOMAIN,) * 4)

lockedRecipe = """class GroupTest(GroupRecipe):
    name = 'group-test'
    version = '1.0.0'

    autoResolve = False

    def setup(r):
        r.setLabelPath('testproject.%s@rpl:devel')
        r.add('testcase', '/testproject.%s@rpl:devel/1.0-1-1', '', groupName = 'group-test')
""" % ((MINT_PROJECT_DOMAIN,) * 2)

packageRecipe = """
class testRecipe(PackageRecipe):
    name = "test"
    version = "1.0"
    clearBuildReqs()

    def setup(self):
	self.Create("/etc/file")
        self.Create("/usr/lib/file")
        self.ComponentSpec('runtime', '/etc/')
        self.ComponentRequires({'lib': set()})
"""

redirectBaseRecipe = """
class testRedirect(PackageRecipe):
    name = "redirect"
    version = "0.1"
    clearBuildReqs()

    def setup(self):
	self.Create("/etc/base")
        self.Create("/usr/lib/base")
        self.ComponentSpec('runtime', '/etc/')
        self.ComponentRequires({'lib': set()})
"""

redirectRecipe = """
class testRedirect(RedirectRecipe):
    name = 'redirect'
    version = '1.0'

    def setup(r):
        l = "testproject.%s@rpl:devel"
        r.addRedirect("test", l)
""" % (MINT_PROJECT_DOMAIN,)

def addTestTrove(groupTrove, trvName,
        trvVersion = '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1',
        trvFlavor='1#x86|5#use:~!kernel.debug:~kernel.smp',
        subGroup = ''):
    return groupTrove.addTrove(trvName, trvVersion, trvFlavor,
                               subGroup, False, False, False)


class GroupTroveTest(fixtures.FixturedUnitTest):
    @testsuite.context("quick")
    @fixtures.fixture("Full")
    def testBasicAttributes(self, db, data):
        client = self.getClient("owner")
        projectId = data['projectId']
        groupTrove = client.getGroupTrove(data['groupTroveId'])

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

    @fixtures.fixture("Full")
    def testUpstreamVersions(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        assert(groupTrove.upstreamVersion == '1.0.0')

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

    @fixtures.fixture("Full")
    def testVersionLock(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        trvId = addTestTrove(groupTrove, 'testcase')

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is False)

        assert(gTrv['trvVersion'] == '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel')

        groupTrove.setTroveVersionLock(trvId, True)

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['versionLock'] is True)

        assert(gTrv['trvVersion'] == '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0-1-1')
        assert(gTrv['trvLabel'] == 'testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel')

    @fixtures.fixture("Full")
    def testAutoResolve(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        assert(groupTrove.autoResolve is False)

        groupTrove.setAutoResolve(True)
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.autoResolve is True)

        groupTrove.setAutoResolve(False)
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.autoResolve is False)

    @fixtures.fixture("Full")
    def testFlavorLock(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        trvId = addTestTrove(groupTrove, 'testcase')
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

    @fixtures.fixture("Full")
    def testListGroupTroveItems(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        trvId = addTestTrove(groupTrove, "testcase")
        trv2Id = addTestTrove(groupTrove, "testcase2")

        if len(groupTrove.listTroves()) != 2:
            self.fail("listTroves returned the wrong number of results, we expected two.")

        groupTrove.delTrove(trv2Id)

        if len(groupTrove.listTroves()) != 1:
            self.fail("groupTrove.delTrove didn't work.")

    @fixtures.fixture("Full")
    def testGroupTroveDesc(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        desc = 'A different description'

        groupTrove.setDesc(desc)

        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.description == desc)

    @fixtures.fixture("Full")
    def testSubGroup(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()
        trvId = addTestTrove(groupTrove, "testcase")

        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['subGroup'] == 'group-test')

        groupTrove.setTroveSubGroup(trvId, "group-foo")
        gTrv = groupTrove.getTrove(trvId)
        assert(gTrv['subGroup'] == 'group-foo')

    @fixtures.fixture("Full")
    def testUpstreamVersion(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        groupTroveId = groupTrove.getId()

        assert(groupTrove.upstreamVersion == '1.0.0')

        groupTrove.setUpstreamVersion("1.0.1")
        groupTrove = client.getGroupTrove(groupTroveId)
        assert(groupTrove.upstreamVersion == '1.0.1')

    @fixtures.fixture("Full")
    def testBadParams(self, db, data):
        client = self.getClient("owner")
        projectId = data['projectId']

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

        groupTrove = client.getGroupTrove(data['groupTroveId'])

        try:
            groupTrove.setUpstreamVersion('1-0.0')
            self.fail("Group Trove with bad version was allowed (modify)")
        except grouptrove.GroupTroveVersionError:
            pass

    @fixtures.fixture("Full")
    def testPermissions(self, db, data):
        client = self.getClient("nobody")
        adminClient = self.getClient("admin")
        adminClient.hideProject(data['projectId'])

        groupTroveId = data['groupTroveId']
        groupTrove = adminClient.getGroupTrove(groupTroveId)

        trvId = addTestTrove(groupTrove, 'testtrove')

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
        client = self.getClient("developer")
        client.server.getGroupTrove(groupTroveId)
        client.server.delGroupTroveItem(trvId)

        trvId = addTestTrove(groupTrove, 'testtrove')

        # manipulate items as owner
        client = self.getClient("owner")
        client.server.getGroupTrove(groupTroveId)
        client.server.delGroupTroveItem(trvId)

    @fixtures.fixture("Full")
    def testMultipleAdditions(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        addTestTrove(groupTrove, "testcase")
        try:
            addTestTrove(groupTrove, "testcase")
        except DuplicateItem:
            pass
        else:
            self.fail("GroupTrove.addTrove allowed a duplicate entry."
                      "addTrove relies on a unique index,"
                      "please check that it's operative.")

    @fixtures.fixture("Full")
    def testDuplicateLabels(self, db, data):
        trvVersion = '/foo.' + MINT_PROJECT_DOMAIN + \
            '@rpl:devel/1.0-1-1'

        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        addTestTrove(groupTrove, "testcase", trvVersion = trvVersion)
        addTestTrove(groupTrove, "testcase2", trvVersion = trvVersion)
        assert (groupTrove.getLabelPath() == ['foo.' + \
                MINT_PROJECT_DOMAIN + '@rpl:devel'])

    @fixtures.fixture("Full")
    def testEmptyCook(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        assert(len(groupTrove.listTroves()) == 0)

        try:
            groupTrove.startCookJob("1#x86")
        except server.GroupTroveEmpty:
            pass
        else:
            self.fail("allowed to start an empty cook job")

        trvId = addTestTrove(groupTrove, "testcase")

        assert(len(groupTrove.listTroves()) == 1)

    @fixtures.fixture("Full")
    def testSourceGroups(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        v = versions.ThawVersion( \
            "/testproject." + MINT_PROJECT_DOMAIN + \
            "@rpl:devel/123.0:1.0-1-1")

        # should not be allowed to add source components to groups
        self.assertRaises(grouptrove.GroupTroveNameError, addTestTrove,
                          groupTrove, "test:source", v.asString())

    @fixtures.fixture("Full")
    def testTroveInGroupVersions(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        trvId = addTestTrove(groupTrove, "testcase")

        # exact version, unlocked
        self.failIf(not groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', ""),
                     "Group Trove didn't identify correct trove")

        # mismatch version, but unlocked
        self.failIf(not groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/5.0-1-1', ""),
                     "Group Trove didn't identify unlocked version")

        # mismatched branch, unlocked
        self.failIf(groupTrove.troveInGroup( \
            "testcase", '/testproject.neverland@rpl:devel/5.0-1-1', ""),
                     "Group Trove didn't identify locked version")
        groupTrove.setTroveVersionLock(trvId, True)

        # newer version, locked
        self.failIf(groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/5.0-1-1', ""),
                     "Group Trove didn't identify locked version")

        # exact version, locked
        self.failIf(not groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', ""),
                     "Group Trove didn't identify correct trove")

    @fixtures.fixture("Full")
    def testAgnosticTroveInGroup(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveId = groupTrove.getId()

        trvId = addTestTrove(groupTrove, "testcase")

        # agnostic trove, unlocked
        self.failIf(not groupTrove.troveInGroup("testcase"),
                    "Group Trove didn't identify agnostic trove")

        groupTrove.setTroveVersionLock(trvId, True)
        # agnostic trove, version locked
        self.failIf(not groupTrove.troveInGroup("testcase"),
                    "Group Trove didn't identify agnostic trove (ver lock)")

        groupTrove.setTroveUseLock(trvId, True)
        # agnostic trove, Use locked
        self.failIf(not groupTrove.troveInGroup("testcase"),
                    "Group Trove didn't identify agnostic trove")

        groupTrove.setTroveUseLock(trvId, True)
        # agnostic trove, IS locked
        self.failIf(not groupTrove.troveInGroup("testcase"),
                    "Group Trove didn't identify agnostic trove (IS lock)")

        self.failIf(groupTrove.troveInGroup("notthere"),
                    "Group Trove identified bad agnostic trove")

    @fixtures.fixture("Full")
    def testTroveInGroupIS(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        trvId = addTestTrove(groupTrove, "testcase")
        # mismatch arch, unlocked
        self.failIf(not groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', "1#x86_64"),
                     "Group Trove didn't identify mismatched unlocked arch")

        groupTrove.setTroveInstSetLock(trvId, True)

        # mismatch arch, locked
        self.failIf(groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', "1#x86_64"),
                     "Group Trove didn't identify mismatched locked arch")

        # match arch, locked
        self.failIf(not groupTrove.troveInGroup( \
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', "1#x86"),
                     "Group Trove didn't identify correct locked arch")

    @fixtures.fixture("Full")
    def testTroveInGroupUse(self, db, data):
        client = self.getClient("owner")
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        trvId = addTestTrove(groupTrove, "testcase")

        # match, unlocked
        self.failIf(not groupTrove.troveInGroup(\
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', '5#use:~!kernel.debug:~kernel.smp'),
                     "Group Trove didn't identify unlocked use flags")

        groupTrove.setTroveUseLock(trvId, True)

        # match, locked
        self.failIf(not groupTrove.troveInGroup(\
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', '5#use:~!kernel.debug:~kernel.smp'),
                     "Group Trove didn't identify correct locked use flags")

        # mismatch, locked
        self.failIf(groupTrove.troveInGroup(\
            "testcase", '/testproject.' + MINT_PROJECT_DOMAIN +
            '@rpl:devel/1.0-1-1', '5#use:~!kernel.debug:kernel.smp'),
                     "Group Trove didn't identify mismatched locked use flags")

    @fixtures.fixture('Full')
    def testComponentRemoval(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        self.failIf(groupTrove.listRemovedComponents() != [],
                    "Initial set of removed components not empty")
        groupTrove.removeComponents(['devel', 'doc'])
        self.failIf(groupTrove.listRemovedComponents() != ['devel', 'doc'],
                    "components didn't get removed")
        groupTrove.allowComponents(['devel'])
        self.failIf(groupTrove.listRemovedComponents() != ['doc'],
                    "component didn't get re-added")

    @fixtures.fixture('Full')
    def testComponentSetRemoved(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        self.failIf(groupTrove.listRemovedComponents() != [],
                    "Initial set of removed components not empty")
        groupTrove.removeComponents(['devel', 'doc'])
        self.failIf(groupTrove.listRemovedComponents() != ['devel', 'doc'],
                    "components didn't get removed")
        groupTrove.setRemovedComponents(['devel'])
        self.failIf(groupTrove.listRemovedComponents() != ['devel'],
                    "component didn't get properly set")

    @fixtures.fixture('Full')
    def testComponentSetRemovedAtomic(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        self.failIf(groupTrove.listRemovedComponents() != [],
                    "Initial set of removed components not empty")
        groupTrove.removeComponents(['devel', 'doc'])
        self.failIf(groupTrove.listRemovedComponents() != ['devel', 'doc'],
                    "components didn't get removed")
        # the point isn't the exception, it's the effect on the db.
        self.assertRaises(ParameterError,
                          groupTrove.setRemovedComponents,
                          ['sirnotappearinginthislist'])
        self.failIf(groupTrove.listRemovedComponents() != ['devel', 'doc'],
                    "setRemovedComponents is not atomic")

    @fixtures.fixture('Full')
    def testMissingComponentAllow(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        self.failIf(groupTrove.listRemovedComponents() != [],
                    "Initial set of removed components not empty")
        groupTrove.allowComponents(['devel'])
        self.failIf(groupTrove.listRemovedComponents() != [],
                    "Incorrect results from spurious removal")

    @fixtures.fixture('Full')
    def testDoubleComponentRemove(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        groupTrove.removeComponents(['devel'])
        # remove twice
        groupTrove.removeComponents(['devel'])
        cu = db.cursor()
        cu.execute("SELECT COUNT(*) FROM GroupTroveRemovedComponents")
        self.failIf(cu.fetchone()[0] != 1,
                    "Group Trove allowed double removal of component")

    @fixtures.fixture('Full')
    def testRemovedComponentRecipe(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        groupTrove.removeComponents(['devel', 'doc'])
        self.failIf(groupTrove.getRecipe() != refCompRecipe,
                    "Recipe with removed components isn't correct.")

    @fixtures.fixture('Full')
    def testIllegalRemoval(self, db, data):
        ownerId = data['owner']
        projectId = data['projectId']
        groupTroveId = data['groupTroveId']
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(groupTroveId)
        self.assertRaises(ParameterError,
                          groupTrove.removeComponents, ['notarealcomponent'])

    @fixtures.fixture('Full')
    def testCleanup(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        assert client.server._server.cleanupGroupTroves() is not None

    @fixtures.fixture('Full')
    def testLabelPath(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])
        assert groupTrove.getLabelPath() == ['foo.%s@rpl:devel' % MINT_PROJECT_DOMAIN]

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])
        self.assertRaises(PermissionDenied,
                          client.server._server.getGroupTroveLabelPath,
                          groupTrove.id)

    @fixtures.fixture('Full')
    def testGetRecipeAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])
        self.assertRaises(PermissionDenied, client.server._server.getRecipe,
                          data['groupTroveId'])

    @fixtures.fixture('Full')
    def testSetAutoResolveAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])
        self.assertRaises(PermissionDenied,
                          client.server._server.setGroupTroveAutoResolve,
                          data['groupTroveId'], True)

    @fixtures.fixture('Full')
    def testListGrpTrvAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])
        self.assertRaises(PermissionDenied,
                          client.server._server.listGroupTrovesByProject,
                          data['projectId'])

    @fixtures.fixture('Full')
    def testCreateGrpTrvAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises(PermissionDenied, client.createGroupTrove,
                          data['projectId'], 'foo', '1.0.0', '', False)

    @fixtures.fixture('Full')
    def testDeleteGrpTrvAccess(self, db, data):
        client = self.getClient('user')

        # bogus call to prime client
        client.getUser(data['user'])
        self.assertRaises(PermissionDenied, client.deleteGroupTrove,
                          data['groupTroveId'])

    @fixtures.fixture('Full')
    def testGrpTrvDescAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises(PermissionDenied,
                          client.server._server.setGroupTroveDesc,
                          data['groupTroveId'], 'foo')

    @fixtures.fixture('Full')
    def testGrpTrvVerAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises(PermissionDenied,
                          client.server._server.setGroupTroveUpstreamVersion,
                          data['groupTroveId'], '1.0.0')

    @fixtures.fixture('Full')
    def testListGrpTrvItemsAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.listGroupTroveItemsByGroupTrove,
            data['groupTroveId'])

    @fixtures.fixture('Full')
    def testTrvInGrpTrvItemsAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.troveInGroupTroveItems,
            data['groupTroveId'], 'foo', '/test@rpl:devel/1-1-1', '')

    @fixtures.fixture('Full')
    def testGrpTrvItemVerLckAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.setGroupTroveItemVersionLock,
            groupTroveItemId, True)

    @fixtures.fixture('Full')
    def testGrpTrvItemUseLckAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.setGroupTroveItemUseLock,
            groupTroveItemId, True)

    @fixtures.fixture('Full')
    def testGrpTrvItemISLckAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.setGroupTroveItemInstSetLock,
            groupTroveItemId, True)

    @fixtures.fixture('Full')
    def testDelGrpTrvItemAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.delGroupTroveItem, groupTroveItemId)

    @fixtures.fixture('Full')
    def testGetGrpTrvItemAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.getGroupTroveItem, groupTroveItemId)

    @fixtures.fixture('Full')
    def testSetGrpTrvItemSubGrpAccess(self, db, data):
        client = self.getClient('owner')
        groupTrove = client.getGroupTrove(data['groupTroveId'])

        groupTroveItemId = groupTrove.addTrove( \
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.setGroupTroveItemSubGroup, groupTroveItemId,
            'group-test')

    @fixtures.fixture('Full')
    def testAddGrpTrvItemAccess(self, db, data):
        client = self.getClient('user')
        # bogus call to prime client
        client.getUser(data['user'])

        self.assertRaises( \
            PermissionDenied,
            client.server._server.addGroupTroveItem, data['groupTroveId'],
            'foo', '/test.rpath.local@rpl:devel/1.0.0-1-1', '', '',
            False, False, False)

class GroupTroveTestConary(MintRepositoryHelper):
    def makeCookedTrove(self, branch = 'rpl:devel', hostname = 'testproject'):
        l = versions.Label("%s.%s@%s" % (hostname, MINT_PROJECT_DOMAIN, branch))
        self.makeSourceTrove("testcase", testRecipe, l)
        self.cookFromRepository("testcase", l, ignoreDeps = True)

    def testGetRecipe(self):
        def bogusResolve(a, b, c, d):
            return []

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeCookedTrove('rpl:devel')
        trvId = addTestTrove(groupTrove, "testcase")
        assert(groupTrove.getRecipe() == refRecipe)

        groupTrove.setTroveVersionLock(trvId, True)
        assert(groupTrove.getRecipe() == lockedRecipe)
        groupTrove.setTroveVersionLock(trvId, False)

        # test the "fancy-flavored" group-core hack:
        # XXX: this has to connect to the outside world and hit conary.rpath.com
        grpTrvItem = groupTrove.addTrove(\
            'group-core', '/conary.rpath.com@rpl:devel//1/1.0-0.5-10',
            '1#x86', 'group-test', False, True, True)

        assert(groupTrove.getRecipe() == groupsRecipe)

    def testGetRecipeRedir(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeCookedTrove('rpl:devel')
        trvId = addTestTrove(groupTrove, "testcase")
        assert(groupTrove.getRecipe() == refRecipe)

        groupTrove.setTroveVersionLock(trvId, True)
        assert(groupTrove.getRecipe() == lockedRecipe)
        groupTrove.setTroveVersionLock(trvId, False)

        self.build(packageRecipe, "testRecipe")
        self.build(redirectBaseRecipe, "testRedirect")

        trv = self.build(redirectRecipe, "testRedirect")

        addTestTrove(groupTrove, trv.name(), str(trv.version()),
                          trv.flavor().freeze())

        assert(groupTrove.getRecipe() == refRedirRecipe)

    def testAddByProject(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        groupProjectId = self.newProject(client, name = 'Foo',
                                         hostname = 'foo')
        groupProject = client.getProject(groupProjectId)

        cu = self.db.cursor()
        cu.execute('UPDATE Labels SET label=? WHERE projectId=?',
                   'testproject.' + MINT_PROJECT_DOMAIN + '@foo:bar', 
                   groupProjectId)
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
            refTrvVersion = '/testproject.%s@%s/1.0-1-1' % \
                    (MINT_PROJECT_DOMAIN, branch)

            self.captureAllOutput(self.makeCookedTrove, branch)

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

    def testCookAutoRecipe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + \
                    "@rpl:devel"),
            ignoreDeps = True)

        trvId = addTestTrove(groupTrove, "testcase")

        self.makeSourceTrove("group-test", groupTrove.getRecipe())
        self.cookFromRepository("group-test",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + \
                    "@rpl:devel"))

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label("testproject." + \
                MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == ['group-test'])

    def waitForCommit(self, project, troveList):
        iters = 0
        while True:
            time.sleep(0.5)
            iters += 1
            if [x[:2] for x in project.getCommits()] == troveList:
                break
            if iters > 30:
                self.fail("commits didn't show up")

    def testCookOnServer(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)
        groupTroveId = groupTrove.getId()

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + \
                    "@rpl:devel"),
            ignoreDeps = True)

        trvId = addTestTrove(groupTrove, "testcase")
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
        assert(trvVersion == '/testproject.' + MINT_PROJECT_DOMAIN + \
                '@rpl:devel/1.0.0-2-1')
        assert(trvFlavor == '')

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        troveNames = nc.troveNames(versions.Label(
            "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"))
        assert(troveNames == ['testcase', 'testcase:runtime', 'group-test',
                              'group-test:source', 'testcase:source'])

        groupTroves = client.server.getGroupTroves(projectId)
        assert(groupTroves == ['group-test'])

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

        v = versions.ThawVersion("/testproject." + MINT_PROJECT_DOMAIN + \
                "@rpl:devel/123.0:1.0-1-1")
        v2 = versions.ThawVersion("/testproject." + MINT_PROJECT_DOMAIN + \
                "@rpl:mumble/123.0:1.0-1-1")

        # trove1 on both v and v2, trove2 only on v2
        self.addPackage("trove1", v)
        self.addPackage("trove1", v2, filePrimers = {'devel': 2, 'runtime': 3})
        self.addPackage("trove2", v2)

        trvId = addTestTrove(groupTrove, "trove1", v.asString())
        trvId = addTestTrove(groupTrove, "trove2", v2.asString())
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


    def testGrpTrvConfRes(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)

        # do a full fledged cook. test suite shortcuts will break.
        self.makeSourceTrove("testcase", testRecipe)
        res = self.cookFromRepository("testcase",
                                      versions.Label("testproject." + \
                                                     MINT_PROJECT_DOMAIN + \
                                                     "@rpl:devel"),
                                      ignoreDeps = True)[0]

        groupTrove.addTrove('testcase', res[1], res[2].freeze(), '',
                            False, False, False)
        recipe = groupTrove.getRecipe()
        jobId = groupTrove.startCookJob('1#x86')
        job = client.getJob(jobId)

        isocfg = self.writeIsoGenCfg()
        cookJob = group_trove.GroupTroveCook(client, isocfg, job)
        trvName, trvVersion, trvFlavor = cookJob.write()

        repos = client.server._server._getProjectRepo(project)
        trv = repos.getTrove(*repos.findTrove( \
            versions.VersionFromString(trvVersion).branch().label(),
            (trvName + ":source", None, None))[0])

        pId, fPath, fId, fVer = [x for x in trv.iterFileList() if \
                                 x[1] == 'group-test.recipe'][0]

        mainRepos = self.openRepository()
        newRecipe = mainRepos.getFileContents([(fId, fVer)])[0].get().read()

        self.failIf(newRecipe != recipe,
                    "recipe mangled during group builder cook.")

        # cook again to force a new upstream version
        res = self.cookFromRepository("testcase",
                                      versions.Label("testproject." + \
                                                     MINT_PROJECT_DOMAIN + \
                                                     "@rpl:devel"),
                                      ignoreDeps = True)[0]

        groupTrove = self.createTestGroupTrove(client, projectId,
                                               "group-conflict")
        groupTrove.addTrove('group-test', str(trv.version()),
                            trv.flavor.freeze(), '', False, False, False)

        # force the most extreme conflict. two matches from same branch, but
        # only one is explicit. leave version ulocked to force group_trove to
        # make the decision. the highest version number is the correct choice.
        trvId = groupTrove.addTrove('testcase', res[1], res[2].freeze(), '',
                                    False, False, False)

        recipe = groupTrove.getRecipe()
        jobId = groupTrove.startCookJob('1#x86')
        job = client.getJob(jobId)

        isocfg = self.writeIsoGenCfg()
        cookJob = group_trove.GroupTroveCook(client, isocfg, job)
        trvName, trvVersion, trvFlavor = cookJob.write()

        repos = client.server._server._getProjectRepo(project)
        trv = repos.getTrove(*repos.findTrove( \
            versions.VersionFromString(trvVersion).branch().label(),
            (trvName + ":source", None, None))[0])

        pId, fPath, fId, fVer = [x for x in trv.iterFileList() if \
                                 x[1] == 'group-conflict.recipe'][0]

        mainRepos = self.openRepository()
        newRecipe = mainRepos.getFileContents([(fId, fVer)])[0].get().read()

        self.failIf(recipe + "        r.remove('testcase', '/testproject"
                    ".%s@rpl:devel/1.0-1-1', '', "
                    "groupName='group-conflict')\n\n" % MINT_PROJECT_DOMAIN != newRecipe,
                    "group recipe did not reflect proper conflict resolution.")

    def testSerializeGroupTrove(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)

        addTestTrove(groupTrove, 'test-trove')
        job = groupTrove.startCookJob('1#x86')

        serialized = groupTrove.serialize()

        groupTroveDict = simplejson.loads(serialized)

        assert sorted(groupTroveDict.keys()) == \
            ['UUID', 'description', 'jobData', 'labelPath', 'project',
             'recipe', 'recipeName', 'serialVersion', 'troveItems', 'type',
             'upstreamVersion']
        assert groupTroveDict['project'].keys() == ['hostname', 'name', 'label']


if __name__ == "__main__":
    testsuite.main()

#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import os

import mint_rephelp
from mint.web import project
from mint import database
from mint.web.webhandler import HttpNotFound, HttpMoved
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint import users

from mint_rephelp import MINT_PROJECT_DOMAIN

from repostest import testRecipe
from conary import versions
from conary.lib import util

testDirRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"

    def setup(r):
        r.Create("/temp/foo")
        r.MakeDirs("/temp/directory", mode = 0775)
"""

class rogueReq(object):
    def __init__(self):
        self.err_headers_out = {}
        self.headers_out = {}
        self.uri = ''

class WebProjectTest(mint_rephelp.WebRepositoryHelper):
    def testBuildsPerms(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        # Anonymous
        page = self.assertContent('/project/testproject/builds',
                                  code=[200],
                                  content='Permission Denied',
                                  server=self.getProjectServerHostname())

        self.webLogin('testuser', 'testpass')
        # Logged in
        page = self.assertContent('/project/testproject/builds',
                                  code=[200],
                                  content='href="newBuild"',
                                  server=self.getProjectServerHostname())

    def testBuildsList(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'build 1')
        build.setTrove("group-dist", "/testproject." + \
                           MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1",
                       "1#x86")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setFiles([["file", "file title 1"]])

        self.webLogin('testuser', 'testpass')
        page = self.assertNotContent('/project/testproject/builds',
                                  code=[200],
                                  content='currently in progress',
                                  server=self.getProjectServerHostname())

        job = client.startImageJob(build.getId())
        job.setStatus(jobstatus.RUNNING, 'running message')

        page = self.assertContent('/project/testproject/builds',
                                  code=[200],
                                  content='currently in progress',
                                  server=self.getProjectServerHostname())

    def testGroupPerms(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        # Anonymous
        page = self.assertContent('/project/testproject/newGroup',
                                  code=[200],
                                  content='Permission Denied',
                                  server=self.getProjectServerHostname())

        self.webLogin('testuser', 'testpass')
        # Logged in
        page = self.assertContent('/project/testproject/newGroup',
                                  code=[200],
                                  content='action="createGroup"',
                                  server=self.getProjectServerHostname())

    def testGroupList(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.webLogin('testuser', 'testpass')
        page = self.assertContent('/project/testproject/groups',
                                  code=[200],
                                  content='not currently building a group',
                                  server=self.getProjectServerHostname())

        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        page = self.assertContent('/project/testproject/groups',
                                  code=[200],
                                  content='group-test',
                                  server=self.getProjectServerHostname())

    def testEditGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        self.webLogin('testuser', 'testpass')
        page = self.assertContent('/project/testproject/editGroup?id=%d' \
                                      % groupTrove.id,
                                  code=[200],
                                  content='Save and Cook',
                                  server=self.getProjectServerHostname())

    def testEditGrouprMake(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        rMakeBuild = client.createrMakeBuild('foo')
        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect('/editrMake?id=%d' % rMakeBuild.id,
                                      server=self.getProjectServerHostname())
        assert 'action="editrMake2"' in page.body

        page = self.assertContent('/project/testproject/editGroup?id=%s' \
                                      % groupTrove.id,
                                  code=[200],
                                  content='Save and Cook',
                                  server=self.getProjectServerHostname())

    def testEditGroup2(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        groupTroveItemId = groupTrove.addTrove('foo',
                            '/testproject.rpath.local@rpl:devel/1.0-1-1',
                            '', '', True, False, False)

        self.webLogin('testuser', 'testpass')
        page = self.fetch( \
            '/project/testproject/editGroup2?id=%d&version=1.0.1&action=Save%%20Changes%%20Only&%' \
                'd__versionLock=on' \
                % (groupTrove.id, groupTroveItemId),
            server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert groupTrove.upstreamVersion == '1.0.1'

    def testCloseGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        self.webLogin('testuser', 'testpass')
        page = self.assertContent('/project/testproject/editGroup?id=%d' \
                                      % groupTrove.id,
                                  code=[200],
                                  content='Save and Cook',
                                  server=self.getProjectServerHostname())
        page = self.fetch('/project/testproject/closeCurrentGroup?referer=/',
                          server=self.getProjectServerHostname())
        assert "closeCurrentGroup" not in page.body

    def testDeleteGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        self.webLogin('testuser', 'testpass')
        page = self.assertContent('/project/testproject/editGroup?id=%d' \
                                      % groupTrove.id,
                                  code=[200],
                                  content='Save and Cook',
                                  server=self.getProjectServerHostname())
        page = self.fetch('/project/testproject/deleteGroup',
                          ok_codes = [403],
                          server=self.getProjectServerHostname())
        page = self.fetch('/project/testproject/deleteGroup?id=%d' % \
                              groupTrove.id,
                          server=self.getProjectServerHostname())
        assert 'action="deleteGroup"' in page.body
        groupTrove.refresh()
        page = self.fetch('/project/testproject/deleteGroup?id=%d' \
                              '&confirmed=1' % \
                              groupTrove.id,
                          server=self.getProjectServerHostname())
        self.assertRaises(database.ItemNotFound, groupTrove.refresh)

    def testAddGroupTroveItem(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        self.webLogin('testuser', 'testpass')
        self.fetch('/project/testproject/addGroupTrove' \
                       '?id=%d&trove=test&' \
                       'version=/testproject.rpath.local@rpl:devel/1.0.1-1-1&' \
                       'referer=/project/testproject' % \
                       groupTrove.id,
                   server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert groupTrove.listTroves()

    def testAddGroupTroveItemRef(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        self.webLogin('testuser', 'testpass')
        self.fetch('/project/testproject/addGroupTrove' \
                       '?id=%d&trove=test&' \
                       'version=/testproject.rpath.local@rpl:devel/1.0.1-1-1'% \
                       groupTrove.id,
                   server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert groupTrove.listTroves()

    def testAddGroupTroveItemProj(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)

        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect('/project/testproject/addGroupTrove' \
                                          '?id=%d&trove=test&' \
                                          'projectName=testproject&' \
                                          'referer=/' % \
                                          groupTrove.id,
                                      server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert not groupTrove.listTroves()

    def testDeleteGroupTroveItem(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        groupTroveItemId = groupTrove.addTrove('foo',
                            '/testproject.rpath.local@rpl:devel/1.0-1-1',
                            '', '', True, False, False)

        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect( \
            '/project/testproject/deleteGroupTrove?id=%d&troveId=%d&referer=/' \
                % (groupTrove.id, groupTroveItemId),
            server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert not groupTrove.listTroves()

    def testDeleteGroupTroveItemRef(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        groupTroveItemId = groupTrove.addTrove('foo',
                            '/testproject.rpath.local@rpl:devel/1.0-1-1',
                            '', '', True, False, False)

        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect( \
            '/project/testproject/deleteGroupTrove?id=%d&troveId=%d' \
                % (groupTrove.id, groupTroveItemId),
            server=self.getProjectServerHostname())
        groupTrove.refresh()
        assert not groupTrove.listTroves()

    def testPickArch(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        groupTrove = client.createGroupTrove(projectId, 'group-test', '1.0.0',
                                             'No Description', False)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/editGroup2?id=%d&action=Save%%20and%%20Cook&version=1.0.0' % groupTrove.id,
                          server=self.getProjectServerHostname())
        assert 'Choose an architecture' in page.body

    def testNewBuild(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect('/project/testproject/newBuild',
                                      server=self.getProjectServerHostname())
        assert 'action="saveBuild"' in page.body

    def testEditBuild(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, 'build 1')
        self.webLogin('testuser', 'testpass')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        page = self.fetch('/project/testproject/editBuild?' \
                              'buildId=%d&action=Edit%%20Build' % build.id,
                          server=self.getProjectServerHostname())
        assert 'action="saveBuild"' in page.body

    def testRecreateBuild(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, 'build 1')
        self.webLogin('testuser', 'testpass')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        page = self.fetch('/project/testproject/editBuild?' \
                              'buildId=%d&action=Recreate%%20Build' % build.id,
                          server=self.getProjectServerHostname())
        assert '/project/testproject/build?id=%d' % build.id in page.body

    def testBadAction(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/editBuild?action=Wrong',
                          server=self.getProjectServerHostname())
        # retrieve the session error
        page = self.fetch('/')
        assert 'Invalid action' in page.body

    def testDeleteBuild(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, 'build 1')
        self.webLogin('testuser', 'testpass')
        page = self.fetchWithRedirect('/project/testproject/deleteBuild?id=%d' \
                                          % build.id,
                                      server=self.getProjectServerHostname())
        assert 'action="deleteBuild"' in page.body
        assert 'type="hidden" name="confirmed"' in page.body
        page = self.fetchWithRedirect('/project/testproject/deleteBuild?id=%d' \
                                          '&confirmed=1' % build.id,
                                      server=self.getProjectServerHostname())

        self.assertRaises(database.ItemNotFound, build.refresh)

    def testReleases(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.assertContent('/project/testproject/releases',
                                  code=[200],
                                  content='has no releases',
                                  server=self.getProjectServerHostname())

    def testProjectPage(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'This is a fledgling project' in page.body

    def testBasicTroves(self):
        projectHandler = project.ProjectHandler()
        projectHandler.cfg = self.mintCfg
        util.mkdirChain(os.path.join(self.mintCfg.dataPath, 'config'))
        f = open(os.path.join(self.mintCfg.dataPath, 'config', 'conaryrc'), 'w')
        f.close()
        troveNames, troveDict, metadata, messages = projectHandler._getBasicTroves()
        refNamesRpl1 = ('group-core', 'group-base', 'group-devel',
                        'group-dist-extras', 'group-gnome',
                        'group-kde', 'group-netserver', 'group-xorg')

        refNamesRaa = ('group-raa', )

        for troveName in refNamesRpl1:
            assert troveName in troveNames['conary.rpath.com@rpl:1']
        for troveName in refNamesRaa:
            assert troveName in troveNames['raa.rpath.org@rpl:1']

        self.failIf(messages['conary.rpath.com@rpl:1'] != 'These troves come from rPath Linux on the conary.rpath.com@rpl:1 label')
        self.failIf(set(troveDict.keys()) != set(troveNames['conary.rpath.com@rpl:1'] + troveNames['raa.rpath.org@rpl:1']),
                    "troveDict doesn't match trove names list")
        self.failIf(set(troveDict.keys()) != set(metadata),
                    "trove metadata doesn't match the actual trove list")

    testsuite.context('more_cowbell')
    def testCreateGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        projectHandler = project.ProjectHandler()
        projectHandler.project = client.getProject(projectId)
        projectHandler.userLevel = userlevels.OWNER
        projectHandler.session = {}
        projectHandler.client = client
        projectHandler.cfg = self.mintCfg
        projectHandler.req = rogueReq()

        self.assertRaises(HttpMoved, projectHandler.createGroup,
                          auth = ('testuser', 'testpass'),
                          groupName = 'foo', version = '1.0.0',
                          description = '',
                          initialTrove = [ \
                'group-test testproject.rpath.local@rpl:devel/1.0.1-1-2 []'])
        assert not projectHandler.session['errorMsgList']

    testsuite.context('more_cowbell')
    def testBadGroupParams(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        projectHandler = project.ProjectHandler()
        projectHandler.project = client.getProject(projectId)
        projectHandler.userLevel = userlevels.OWNER
        projectHandler.session = {}
        projectHandler.client = client
        projectHandler.cfg = self.mintCfg
        projectHandler.req = rogueReq()
        projectHandler.auth = users.Authorization(\
            token = ('testuser', 'testpass'))
        projectHandler.isWriter = True
        projectHandler.isOwner = True
        projectHandler.SITE = self.mintCfg.siteHost + self.mintCfg.basePath
        projectHandler.searchType = None
        projectHandler.searchTerms = ''
        projectHandler.inlineMime = None
        projectHandler.infoMsg = None
        projectHandler.errorMsgList = []

        page = projectHandler.createGroup(auth = ('testuser', 'testpass'),
                                          groupName = '', version = '',
                                          description = '', initialTrove = [])
        assert projectHandler.session['errorMsgList'] == \
            ['Error parsing version string: ',
             'Invalid group trove name: group-']


class DirectProjectTest(testsuite.TestCase):
    testsuite.context('more_cowbell')
    def testBadProject(self):
        class BadClient(object):
            def getProjectByHostname(self, *args, **kwargs):
                raise HttpNotFound

        projectHandler = project.ProjectHandler()
        projectHandler.cmd = 'foo/browse'
        projectHandler.client = BadClient()
        self.assertRaises(HttpNotFound, projectHandler.handle, {})

    def testUserDict(self):
        members = ((1, 'bob', userlevels.USER),
                   (2, 'alice', userlevels.OWNER),
                   (3, 'eve', userlevels.DEVELOPER))
        userDict = project.getUserDict(members)
        refDict = {userlevels.OWNER: [(2, 'alice')],
                   userlevels.DEVELOPER: [(3, 'eve')],
                   userlevels.USER: [(1, 'bob')]}
        self.failIf(userDict != refDict,
                    "getUserDict returned bad results")




if __name__ == "__main__":
    testsuite.main()

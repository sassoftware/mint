#!/usr/bin/python2.4
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import os
import re
import shutil
import types
import copy

import mint_rephelp
import fixtures
from mint.web import project
from mint.web import site
from mint import database
from mint.web.webhandler import HttpNotFound, HttpMoved
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint import users
from mint import helperfuncs

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

class session(dict):
    def save(self):
        pass

class WebProjectBaseTest(mint_rephelp.WebRepositoryHelper):
    def _setupProjectHandler(self):

        def _addErrors(self, msg):
            if 'errorMsgList' not in self.session:
                self.session['errorMsgList'] = []
            self.session['errorMsgList'].append(msg)

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        projectHandler = project.ProjectHandler()
        projectHandler.projectId = projectId
        projectHandler.project = client.getProject(projectId)
        projectHandler.userLevel = userlevels.OWNER
        projectHandler.client = client
        projectHandler.session = session()
        projectHandler.cfg = self.mintCfg
        projectHandler.req = rogueReq()
        projectHandler.auth = users.Authorization(\
            token = ('testuser', 'testpass'))
        projectHandler.isWriter = True
        projectHandler.isOwner = True
        projectHandler.SITE = self.mintCfg.siteHost + self.mintCfg.basePath
        projectHandler.basePath = self.mintCfg.basePath
        projectHandler.searchType = None
        projectHandler.searchTerms = ''
        projectHandler.infoMsg = None
        projectHandler.errorMsgList = []
        projectHandler.currentVersion = projectHandler.client.addProductVersion(projectHandler.projectId, self.mintCfg.namespace, "version1", "Fluff description")
        projectHandler._setCurrentProductVersion(projectHandler.currentVersion)
        projectHandler.versions = projectHandler.client.getProductVersionListForProduct(projectHandler.projectId)
        projectHandler.latestRssNews = {}
        projectHandler.toUrl = self.mintCfg.basePath
        projectHandler.groupTrove = None
        projectHandler.membershipReqsList = None
        projectHandler._addErrors = types.MethodType(_addErrors,
            projectHandler, projectHandler.__class__)

        return projectHandler

    def _setupSiteHandler(self):

        def _addErrors(self, msg):
            if 'errorMsgList' not in self.session:
                self.session['errorMsgList'] = []
            self.session['errorMsgList'].append(msg)

        client, userId = self.quickMintUser('testuser', 'testpass')
        siteHandler = site.SiteHandler()
        siteHandler.client = client
        siteHandler.cfg = self.mintCfg
        siteHandler.req = rogueReq()
        siteHandler.req.hostname = self.mintCfg.siteHost.split(':')[0]
        siteHandler.auth = users.Authorization(\
            token = ('testuser', 'testpass'))
        siteHandler.auth.authorized = True
        siteHandler.SITE = self.mintCfg.siteHost + self.mintCfg.basePath
        siteHandler.basePath = self.mintCfg.basePath
        siteHandler.searchType = None
        siteHandler.searchTerms = ''
        siteHandler.infoMsg = None
        siteHandler.errorMsgList = []
        siteHandler.session = session()
        siteHandler.latestRssNews = {}
        siteHandler.membershipReqsList = None
        siteHandler._addErrors = types.MethodType(_addErrors,
            siteHandler, siteHandler.__class__)

        return siteHandler,  siteHandler.auth


class WebProjectTest(WebProjectBaseTest):
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
                                  content='HREF="newBuild"',
                                  server=self.getProjectServerHostname())

    def testBuildsList(self):
        raise testsuite.SkipTestException("startImageJob returns None")
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
                                  content='ACTION="createGroup"',
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
        assert 'ACTION="deleteGroup"' in page.body
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
        assert 'ACTION="saveBuild"' in page.body

    def testNewBuildUnknownArch(self):
        raise testsuite.SkipTestException("startImageJob returns None")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')

        # totally bogus is: field
        v1 = "/testproject.%s@rpl:linux/1.0-1-1" % MINT_PROJECT_DOMAIN
        f1 = 'is: foomatic'

        self.addComponent("testtrove:runtime", v1, f1)
        self.addCollection("testtrove", v1, [":runtime"],
                defaultFlavor = f1)

        self.addCollection("group-dist", v1, [("testtrove", v1)],
                defaultFlavor = f1)

        self.setServer(self.getProjectServerHostname(), self.port)
        page = self.fetchWithRedirect('/project/testproject/newBuild')
        page.postForm(1, self.fetchWithRedirect,
                {'buildtype': '2',
                 'distTroveSpec': 'group-dist=/testproject.%s@rpl:linux/0.0:1.0-1-1[is: foomatic]' % MINT_PROJECT_DOMAIN,
                 'name': 'Test build with bad arch',
                 'desc': '',
                 'action': 'saveBuild'})
        page = page.fetchWithRedirect('/project/testproject/builds')
        self.failUnless('foomatic' in page.body)

    def testEditBuild(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, 'build 1')
        self.webLogin('testuser', 'testpass')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        page = self.fetch('/project/testproject/editBuild?' \
                              'buildId=%d&action=Edit%%20Image' % build.id,
                          server=self.getProjectServerHostname())
        assert 'ACTION="saveBuild"' in page.body

    def testRecreateBuild(self):
        raise testsuite.SkipTestException("startImageJob returns None")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, 'build 1')
        self.webLogin('testuser', 'testpass')
        build.setTrove("group-trove",
                         "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        page = self.fetch('/project/testproject/editBuild?' \
                              'buildId=%d&action=Recreate%%20Image' % build.id,
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
        assert 'ACTION="deleteBuild"' in page.body
        assert 'TYPE="hidden" NAME="confirmed"' in page.body
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
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'fledgling' in page.body

    def testProjectPageVersionSelectorAnonymous(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        self.failIf('Version:' in page.body)

        versionId = client.addProductVersion(projectId, self.mintCfg.namespace, "version1", "Fluff description")
        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        self.failIf('Version:' in page.body)
        self.failIf('No versions available' in page.body)

    def _projectPageVersionSelector(self, level, shouldSee=True):
        client, ownerId = self.quickMintUser('testowner', 'testpass')
        userclient, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.addMemberById(ownerId, userlevels.OWNER)
        project.addMemberById(userId, level)
        self.webLogin('testuser', 'testpass')

        if shouldSee:
            page = self.fetchWithRedirect('/project/testproject',
                                          server=self.getProjectServerHostname())
            assert 'No versions available' in page.body

            versionId = client.addProductVersion(projectId, self.mintCfg.namespace, "version1", "Fluff description")
            self.fetch('/project/testproject/setProductVersion?versionId=%d&redirect_to=/foo' % versionId,
                    server=self.getProjectServerHostname())
            page = self.fetchWithRedirect('/project/testproject',
                                          server=self.getProjectServerHostname())
            assert 'ID="versionSelectorForm"' in page.body
            assert '<OPTION SELECTED VALUE="%d">' % versionId in page.body
        else:
            page = self.fetchWithRedirect('/project/testproject',
                                          server=self.getProjectServerHostname())
            self.failIf('Version:' in page.body)
            self.failIf('No versions available' in page.body)


    def testProjectPageVersionSelectorDeveloper(self):
        self._projectPageVersionSelector(userlevels.DEVELOPER)

    def testProjectPageVersionSelectorOwner(self):
        self._projectPageVersionSelector(userlevels.OWNER)

    def testProjectPageVersionSelectorUser(self):
        self._projectPageVersionSelector(userlevels.USER, shouldSee=False)

    def testProjectPageManageNotOwner(self):
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'create package' not in page.body.lower()
        assert not re.search('create a <a href=".*newpackage">new package</a>', page.body.lower())
        assert 'manage this %s'%pText.lower() not in page.body.lower()

    def testProjectPageManageOwner(self):
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.addMemberById(userId, userlevels.OWNER)
        self.webLogin('testuser', 'testpass')

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'create package' in page.body.lower()
        assert re.search('create a <a href=".*newpackage">new package</a>', page.body.lower())
        assert 'manage this %s'%pText.lower() in page.body.lower()

    def testBasicTroves(self):
        raise testsuite.SkipTestException("This test relies on external repositories!")
        projectHandler = project.ProjectHandler()
        projectHandler.cfg = self.mintCfg
        util.mkdirChain(os.path.join(self.mintCfg.dataPath, 'config'))
        f = open(os.path.join(self.mintCfg.dataPath, 'config', 'conaryrc'), 'w')
        f.close()
        troveNames, troveDict, metadata, messages = projectHandler._getBasicTroves()
        refNamesRpl1 = ('group-appliance-platform', 'group-base',
                        'group-devel', 'group-dist-extras', 'group-gnome',
                        'group-kde', 'group-netserver', 'group-xorg')

        refNamesRaa = ('group-raa', )

        for troveName in refNamesRpl1:
            assert troveName in troveNames['conary.rpath.com@rpl:1']

        self.failIf(messages['conary.rpath.com@rpl:1'] != 'These groups come from rPath Linux on the conary.rpath.com@rpl:1 label')

        self.failIf(set(troveDict.keys()) != set(metadata),
                    "trove metadata doesn't match the actual trove list")

        self.failIf(set(refNamesRpl1) != set(troveNames['conary.rpath.com@rpl:1']), "troveDict doesn't match trove names list")
        self.failIf(set(refNamesRaa) != set(troveNames['raa.rpath.org@rpath:raa-2']), "troveDict doesn't match trove names list")

        self.assertEquals(set(troveDict.keys()), set(refNamesRaa + refNamesRpl1))


    testsuite.context('more_cowbell')
    def testCreateGroup(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        projectHandler = project.ProjectHandler()
        projectHandler.project = client.getProject(projectId)
        projectHandler.userLevel = userlevels.OWNER
        projectHandler.session = session()
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


    @testsuite.context('more_cowbell')
    def testBadGroupParams(self):
        projectHandler = self._setupProjectHandler()
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


class FixturedProjectTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.ph = project.ProjectHandler()
        self.ph.session = session()

        def fakeRedirect(*args, **kwargs):
            raise HttpMoved

        self.ph._redirect = fakeRedirect


    @fixtures.fixture('Full')
    def testResign(self, db, data):
        client = self.getClient("developer")
        p = client.getProject(data['projectId'])

        self.ph.cfg = self.cfg
        self.ph.client = client
        self.ph.project = p
        self.ph.userLevel = userlevels.DEVELOPER

        auth = users.Authorization(userId = data['developer'], authorized = True)
        self.assertRaises(HttpMoved, self.ph.resign, auth = auth,
            confirmed = True, id = data['developer'])


if __name__ == "__main__":
    testsuite.main()

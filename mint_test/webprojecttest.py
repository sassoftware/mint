#!/usr/bin/python
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

from mint_test import mint_rephelp
import fixtures
from mint.web import project
from mint.web import site
from mint.lib import database
from mint.web.webhandler import HttpNotFound, HttpMoved
from mint import jobstatus
from mint import buildtypes
from mint import userlevels
from mint import users
from mint import helperfuncs
from mint import mint_error

from mint_rephelp import MINT_PROJECT_DOMAIN, FQDN

from repostest import testRecipe
from conary import versions
from conary.lib import util

from testutils import mock


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
        projectHandler.toUrl = self.mintCfg.basePath
        projectHandler.baseUrl = 'http://%s%s' % (FQDN, self.mintCfg.basePath)
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
        siteHandler.membershipReqsList = None
        siteHandler.baseUrl = 'http://%s%s' % (FQDN, self.mintCfg.basePath)
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
                                  content='This product contains no images.',
                                  server=self.getProjectServerHostname())

        self.webLogin('testuser', 'testpass')
        # Logged in
        page = self.assertContent('/project/testproject/builds',
                                  code=[200],
                                  content='HREF="newBuild"',
                                  server=self.getProjectServerHostname())

    def testImagelessBuild(self):
        #raise testsuite.SkipTestException("startImageJob returns None")
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'build 1')
        build.setTrove("group-dist", "/testproject." + \
                           MINT_PROJECT_DOMAIN + "@rpl:devel/0.0:1.1-1-1",
                       "1#x86")
        build.setBuildType(buildtypes.IMAGELESS)
        build.setFiles([["file", "file title 1"]])

        self.webLogin('testuser', 'testpass')
        job = client.startImageJob(build.getId())
        self.failUnlessEqual(job, '0' * 32)
        page = self.assertContent('/project/testproject/builds',
                                  code=[200],
                                  content='Finished',
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
        
    @testsuite.tests('RBL-4225')
    def testDeleteProjectAsAdmin(self):
        client, userId = self.quickMintAdmin('testadmin', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        
        project = client.getProject(projectId)
       
        self.webLogin('testadmin', 'testpass')
        
        page = self.fetch('/project/testproject',
                          server=self.getProjectServerHostname())
        # owner should not see the link
        assert "deleteProject" in page.body
        project.refresh()
        page = self.fetch('/project/testproject/deleteProject?confirmed=1',
                          server=self.getProjectServerHostname())
        self.assertRaises(database.ItemNotFound, client.getProject, projectId)
        
    @testsuite.tests('RBL-4225')
    def testDeleteProjectAsOwner(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        
        project = client.getProject(projectId)
        project.addMemberById(userId, userlevels.OWNER)
       
        self.webLogin('testuser', 'testpass')
        
        page = self.fetch('/project/testproject',
                          server=self.getProjectServerHostname())
        # owner should not see the link
        assert "deleteProject" not in page.body
        project.refresh()
        page = self.fetch('/project/testproject/deleteProject?confirmed=1',
                          server=self.getProjectServerHostname())
        
        assert "Permission Denied".lower() in page.body.lower()

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


def testAs(roleName):
    def decorate(func):
        def wrapper(self, db, data):
            self._use(db, data, roleName)
            return func(self, db, data)
        wrapper.__wrapped_func__ = func
        wrapper.func_name = func.func_name
        return wrapper
    return decorate


class FixturedProjectTest(fixtures.FixturedUnitTest):
    def setUp(self):
        fixtures.FixturedUnitTest.setUp(self)
        self.ph = project.ProjectHandler()
        self.ph.cfg = self.cfg
        self.ph.session = session()
        self.ph.req = mock.MockObject()

        def fakeRedirect(*args, **kwargs):
            raise HttpMoved

        self.ph._redirect = fakeRedirect

    def _use(self, db, data, roleName):
        self.ph.cfg = self.cfg
        self.ph.client = self.client = self.getClient(roleName)
        self.ph.project = self.project = self.client.getProject(data['projectId'])
        self.userId = data[roleName]
        self.ph.userLevel = self.project.getUserLevel(self.userId)
        self.ph.auth = self.auth = users.Authorization(
                userId=self.userId, username=roleName, authorized=True)
        self.ph.baseUrl = 'http://%s%s' % (FQDN, self.cfg.basePath)


    @fixtures.fixture('Full')
    @testAs('developer')
    def testResign(self, db, data):
        self.assertRaises(HttpMoved, self.ph.resign, auth=self.auth,
            confirmed=True, id=data['developer'])

    @fixtures.fixture('Full')
    @testAs('developer')
    def testAdoptPermissions(self, db, data):
        self.assertRaises(HttpMoved, self.ph.adopt, auth=self.auth)
        self.assertEquals(self.project.getUserLevel(self.userId),
                userlevels.DEVELOPER, "User was promoted illegally")
        self.assertEquals(self.ph.session, {'errorMsgList': [
            'You cannot adopt this project at this time.']})


if __name__ == "__main__":
    testsuite.main()

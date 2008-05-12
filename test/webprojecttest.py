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
import copy

import mint_rephelp
import fixtures
from mint.web import project
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
        assert 'action="saveBuild"' in page.body

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
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'This is a fledgling %s'%pText in page.body

    def testProjectPageManageNotOwner(self):
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        page = self.fetchWithRedirect('/project/testproject',
                                      server=self.getProjectServerHostname())
        assert 'manage your %s'%pText.lower() not in page.body.lower()

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
        assert 'manage your %s'%pText.lower() in page.body.lower()

    def testBasicTroves(self):
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

        self.failIf(set(troveDict.keys()) != set(troveNames['conary.rpath.com@rpl:1']), "troveDict doesn't match trove names list")


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


    def _setupProjectHandler(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        projectHandler = project.ProjectHandler()
        projectHandler.projectId = projectId
        projectHandler.project = client.getProject(projectId)
        projectHandler.userLevel = userlevels.OWNER
        projectHandler.client = client
        projectHandler.session = {}
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
        projectHandler.inlineMime = None
        projectHandler.infoMsg = None
        projectHandler.errorMsgList = []

        return projectHandler

    @testsuite.context('more_cowbell')
    def testBadGroupParams(self):
        projectHandler = self._setupProjectHandler()
        page = projectHandler.createGroup(auth = ('testuser', 'testpass'),
                                          groupName = '', version = '',
                                          description = '', initialTrove = [])
        assert projectHandler.session['errorMsgList'] == \
            ['Error parsing version string: ',
             'Invalid group trove name: group-']

    @testsuite.context('more_cowbell')
    def testPackageCreatorUI(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/newPackage',
                server=self.getProjectServerHostname())
        assert 'value="Create Package"' in page.body
        match = re.search('upload_iframe\?sessionHandle=([^;]+);', page.body)
        assert match, "Did not find an id in the page body"
        sessionHandle = match.groups()[0]
        assert sessionHandle, "expected sessionHandle"
        #Make sure it actually did what we asked
        #Get the tempPath
        tmppath = os.path.join(self.mintCfg.dataPath, 'tmp', 'rb-pc-upload-%s' % sessionHandle)
        assert os.path.isdir(tmppath)

    @testsuite.context('more_cowbell')
    def testPackageCreatorIframe(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        self.webLogin('testuser', 'testpass')
        page = self.fetch('/project/testproject/upload_iframe?sessionHandle=foobarbaz;fieldname=upldfile',
                server=self.getProjectServerHostname())
        assert 'action="/cgi-bin/fileupload.cgi?sessionHandle=foobarbaz;fieldname=upldfile"' in page.body
        assert not 'input type="submit"' in page.body.lower(), "Did you forget to remove the submit button?"
        assert 'input type="file" name="uploadfile"' in page.body, 'The file field name is fixed'
        assert 'name="project" value="testproject"' in page.body, 'Make sure the project name is in the form'

    @testsuite.context('more_cowbell')
    def testPackageCreatorInterview(self):
        pcsPath = os.environ.get('PACKAGE_CREATOR_SERVICE_PATH')
        if not pcsPath:
            raise testsuite.SkipTestException( \
                    'Please define PACKAGE_CREATOR_SERVICE_PATH for this test')
        from packagecreatortest import expectedFactories1
        from factorydatatest import dictDef
        from pcreator import factorydata

        from types import MethodType
        self.mock(factorydata, 'defaultSchemaDir',
                os.path.join(pcsPath, 'data'))

        ### All this, just to monkeypatch the client
        projectHandler = self._setupProjectHandler()
        # we need a product version
        # use a nutty word that isn't likely to collide if product version is
        # subsumed into _setupProjectHandler
        versionName = 'supersecretpassword'
        versionId = projectHandler.client.addProductVersion(\
                projectHandler.projectId, versionName, 'this is just a test...')

        projectHandler.req = mint_rephelp.FakeRequest(self.getProjectServerHostname(), 'POST', '/testproject/newPackage')
        fields = {}
        auth = projectHandler.client.checkAuth()
        projectHandler.projectList = projectHandler.client.getProjectsByMember(auth.userId)
        projectHandler.projectDict = {}
        context = {'auth': auth, 'cmd': 'testproject/newPackage', 'client': projectHandler.client, 'fields': fields}
        def fakecreatepackage(s, *args):
            self.assertEquals(args[0], projectHandler.projectId)
            self.assertEquals(args[1], 'foobarbaz')
            self.assertEquals(args[2], 1)
            self.assertEquals(args[3], '')
            return self.dictDef
        self.mock(projectHandler.client, 'newPackage', MethodType(fakecreatepackage, projectHandler.client))

        self.dictDef = expectedFactories1
        func = projectHandler.handle(context)
        page = func(auth=auth, **fields)
        self.failUnless('form action="getPackageFactories"' in page)
        match = re.search('name="sessionHandle" value="[^"]*"', page)

        sessionHandle = match.group().split('"')[-2]
        fields = {
            'sessionHandle': sessionHandle,
            'versionId': str(versionId),
        }
        # our web forms can't do javascript, so we'll fake the upload
        uploadDir = os.path.join(self.mintCfg.dataPath, 'tmp',
                                'rb-pc-upload-%s' % sessionHandle)
        manifestPath = os.path.join(uploadDir, 'uploadfile-index')
        tempfile = os.path.join(uploadDir, 'uploadfile')
        fileName = 'foo-0.1-1.i386.rpm'
        # put a real file there
        shutil.copyfile(os.path.join(self.archiveDir, fileName), tempfile)

        util.mkdirChain(os.path.dirname(manifestPath))
        open(manifestPath, 'w').write('\n'.join(('fieldname=uploadfile',
            'filename=%s' % fileName,
            'tempfile=%s' % tempfile,
            'content-type=multipart/whatever')))

        context = {'auth': auth, 'cmd': 'testproject/getPackageFactories', 'client': projectHandler.client, 'fields': fields}
        func = projectHandler.handle(context)

        #now for a single factory with multiples and ranges
        d = copy.deepcopy(dictDef)
        self.dictDef = [('fakefactory01', None, d, {})]
        page = func(auth=auth, **fields)
        import epdb; epdb.st()

        # FIXME: nothing past this point can be tested until we can properly
        # control where the factories come from. right now that's rb
        self.failUnless('input type="text" id="multiTest_id" value="4" name="multiTest' in page)

        # Get rid of some constraints
        d['dataFields'][0]['constraints'] = [('range', (3, 6))]

        self.dictDef = [('fakefactory01', None, d, {})]
        page = func(auth=auth, **fields)
        self.failUnless('input type="checkbox" id="multiTest_3" value="3" name="multiTest"' in page)
        self.failUnless('input checked="checked" type="checkbox" id="multiTest_4" value="4" name="multiTest"' in page)
        self.failUnless('input type="checkbox" id="multiTest_5" value="5" name="multiTest"' in page)
        self.failIf('input type="checkbox" id="multiTest_2" value="2" name="multiTest"' in page)
        self.failIf('input type="checkbox" id="multiTest_6" value="6" name="multiTest"' in page)

        #take off the multi
        d['dataFields'][0]['multiple'] = False

        self.dictDef = [('fakefactory01', None, d, {})]
        page = func(auth=auth, **fields)
        self.failUnless('input type="radio" id="multiTest_3" value="3" name="multiTest"' in page)
        self.failUnless('input checked="checked" type="radio" id="multiTest_4" value="4" name="multiTest"' in page)
        self.failUnless('input type="radio" id="multiTest_5" value="5" name="multiTest"' in page)
        self.failIf('input type="radio" id="multiTest_2" value="2" name="multiTest"' in page)
        self.failIf('input type="radio" id="multiTest_6" value="6" name="multiTest"' in page)

        #Now a select box
        d['dataFields'][0]['constraints'] = [('range', (1, 31))]
        self.dictDef = [('fakefactory01', None, d, {})]
        page = func(auth=auth, **fields)
        self.failUnless('select name="multiTest" id="multiTest_id"' in page)
        self.failUnless('<option selected="selected" value="4">4</option>' in page)
        self.failUnless('<option value="30">30</option>' in page)

        #Reset multi
        d['dataFields'][0]['multiple'] = True
        self.dictDef = [('fakefactory01', None, d, {})]
        page = func(auth=auth, **fields)
        self.failUnless('select multiple="multiple" name="multiTest" id="multiTest_id"' in page)
        self.failUnless('<option selected="selected" value="4">4</option>' in page)
        self.failUnless('<option value="30">30</option>' in page)

        #Now use a prefilled instead of a default
        d['dataFields'][0]['default'] = None
        self.dictDef = [('fakefactory01', None, d, {'multiTest': 9})]
        page = func(auth=auth, **fields)
        self.failUnless('<option value="4">4</option>' in page)
        self.failUnless('<option selected="selected" value="9">9</option>' in page)
        self.failUnless('<option value="30">30</option>' in page)

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
        self.ph.session = {}

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

    @fixtures.fixture('Full')
    def testProjectActions(self, db, data):
        pText = helperfuncs.getProjectText()
        client = self.getClient("admin")
        p = client.getProject(data['projectId'])

        self.ph.cfg = self.cfg
        self.ph.client = client
        self.ph.project = p
        self.ph.userLevel = userlevels.OWNER

        auth = users.Authorization(userId = data['admin'],
            authorized = True, admin = True)

        self.assertRaises(HttpMoved, self.ph.processProjectAction,
            auth = auth, projectId = p.id, operation = "project_hide")
        p.refresh()
        self.failUnless(p.hidden)

        self.assertRaises(HttpMoved, self.ph.processProjectAction,
            auth = auth, projectId = p.id, operation = "project_hide")
        self.failUnlessEqual(self.ph.session['errorMsgList'], ['%s is already hidden'%pText.title()])

        self.assertRaises(HttpMoved, self.ph.processProjectAction,
            auth = auth, projectId = p.id, operation = "project_unhide")
        p.refresh()
        self.failUnless(not p.hidden)
        self.ph.session = {}

        self.assertRaises(HttpMoved, self.ph.processProjectAction,
            auth = auth, projectId = p.id, operation = "project_unhide")
        self.failUnlessEqual(self.ph.session['errorMsgList'], ['%s is already visible'%pText.title()])

        self.ph.session = {}
        self.assertRaises(HttpMoved, self.ph.processProjectAction,
            auth = auth, projectId = p.id, operation = "project_not_valid")
        self.failUnlessEqual(self.ph.session['errorMsgList'],
            ['Please select a valid %s administration option from the menu'%pText.lower()])


if __name__ == "__main__":
    testsuite.main()

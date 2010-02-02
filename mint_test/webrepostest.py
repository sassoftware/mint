#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#
import os
import shutil
import testsuite
testsuite.setup()

from mint_test import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN

from repostest import testRecipe
from conary import versions
from conary.conaryclient import ConaryClient
from testrunner import pathManager

testDirRecipe = """
class TestCase(PackageRecipe):
    name = "testcase"
    version = "1.0"

    def setup(r):
        r.Create("/temp/foo")
        r.MakeDirs("/temp/directory", mode = 0775)
"""

testTransientRecipe1=r"""\
class TransientRecipe1(PackageRecipe):
    name = 'testcase'
    version = '1.0'
    clearBuildReqs()
    fileText = 'bar\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""
testTransientRecipe2=r"""\
class TransientRecipe2(PackageRecipe):
    name = 'testcase'
    version = '1.1'
    clearBuildReqs()
    fileText = 'blah\n'
    def setup(r):
	r.Create('/foo', contents=r.fileText)
	r.Transient('/foo')
"""


class WebReposTest(mint_rephelp.WebRepositoryHelper):
    def testRepositoryBrowser(self):
        self.startMintServer()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        # first try anonymous browsing
        page = self.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())


        # now try logged-in
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())

        # now try logged-in, as another user user
        page = page.fetchWithRedirect('/logout')
        client, userId = self.quickMintUser('test2', 'test2pass')
        page = self.webLogin('test2', 'test2pass')
        page = page.assertContent('/repos/testproject/browse', code = [200],
            content = 'troveInfo?t=test',
            server = self.getProjectServerHostname())

    def testBrowseTooltips(self):
        raise testsuite.SkipTestException("Not ready for primetime -- yet")
        self.startMintServer()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        page = self.assertContent('/repos/testproject/browse', code = [200],
            content = '1 trove',
            server = self.getProjectServerHostname())

    def testBrowseHiddenProject(self):
        adminClient, adminUserId = self.quickMintAdmin("adminuser", "testpass")

        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')
        project = client.getProject(projectId)

        adminClient.hideProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        # anonymous user should see a 404
        page = self.assertCode('/repos/test/browse', code = 404,
                server = self.getProjectServerHostname())

        # logged-in user should see the browser
        page = self.webLogin('testuser', 'testpass')
        page = page.assertContent('/repos/test/browse', code = [200],
                content = 'troveInfo?t=test',
                server = self.getProjectServerHostname())
        
    @testsuite.tests('RBL-3108')
    def testAdminBrowsePrivateProject(self):
        """
        Make sure admins can browser private products they don't belong to
        """
        adminClient, _ = self.quickMintAdmin("adminuser", "testpass")

        client, _ = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'test')

        adminClient.hideProject(projectId)
        self.makeSourceTrove("testcase", testRecipe)

        self.addComponent("test:runtime", "1.0")
        self.addCollection("test", "1.0", [ ":runtime" ])

        # admin user should see the browser
        page = self.webLogin('adminuser', 'testpass')
        page = page.assertContent('/repos/test/browse', code = [200],
                content = 'troveInfo?t=test',
                server = self.getProjectServerHostname())

    def testBrowseExternalProject(self):
        raise testsuite.SkipTestException("Temporarily skipping - proxy bypass issues")

        client, userId = self.quickMintAdmin("testuser", "testpass")

        self.openRepository(1)
        extProjectId = client.newExternalProject("External Project",
            "external", MINT_PROJECT_DOMAIN, "localhost1@rpl:devel",
            'http://localhost:%d/conary/' % self.servers.getServer(1).port, False)

        self.makeSourceTrove("testcase", testRecipe, buildLabel = versions.Label('localhost1@rpl:devel'))
        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

        # log in and make sure we see the same thing
        page = self.webLogin('testuser', 'testpass')
        page = self.assertCode('/repos/external/browse', code = 200)
        page = page.assertCode('/repos/external/troveInfo?t=testcase:source', code = 200)

    def testTroveInfoPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        # test that missing troves are a 404 not found error
        page = self.fetchWithRedirect('/repos/foo/troveInfo?t=group-foo',
                                      code = [404])

        self.addQuickTestComponent('test:runtime', '3.0-1-1', filePrimer = 3)

        # test that trove info page renders without error
        page = self.assertContent('/repos/testproject/troveInfo?t=test:runtime',
                                  content = 'TITLE="test:runtime"',
                                  server = self.getProjectServerHostname())

    def testTroveInfoPageFlavors(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)


        self.addQuickTestComponent('test:runtime', '3.0-1-1', filePrimer = 3, flavor = "is: x86")
        self.addQuickTestComponent('test:runtime', '3.0-1-1', filePrimer = 3, flavor = "is: x86_64")

        page = self.fetch('/repos/testproject/troveInfo?t=test:runtime',
            server = self.getProjectServerHostname())

        # make sure contents links to both flavors show up
        self.failUnless(';f=1%23x86_64"' in page.body)
        self.failUnless(';f=1%23x86"' in page.body)

    def testReposRSS(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        page = self.fetchWithRedirect('/repos/testproject/browse')

        self.failIf('/repos/testproject/rss' in page.body,
                    "Malformed base path for rss feed on repos page")

    def testFileListDirectories(self):
        self.startMintServer()
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject')
        project = client.getProject(projectId)

        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])

        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/repos/testproject/troveInfo?t=test:runtime')
        fileLink = [x for x in page.getDOM().getByName('a') if x and x[0] == "Show Contents"][0]

        page = self.assertContent('/repos/testproject/' + \
                fileLink.getattr('href'), code = [200],
                content = 'getFile?path=contents0')

    def testDisallowedMethod(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        self.assertCode('/repos/testproject/log', code = 404)

    def testRepoBrowserPermission(self):
        raise testsuite.SkipTestException('Test is not unittest safe')
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client)

        project = client.getProject(projectId)

        cfg = project.getConaryConfig()
        nc = ConaryClient(cfg).getRepos()

        # delete anon access
        nc.deleteAccessGroup(self.cfg.buildLabel, 'anonymous')

        try:
            # check that we get a 403
            self.fetch('/repos/testproject/browse', ok_codes = [403])
        finally:
            # re-add acl. this shouldn't need to be done but seems
            # to be necessary for other unit tests.
            nc.addAccessGroup(self.cfg.buildLabel, 'anonymous')
            nc.addAcl(self.cfg.buildLabel, 'anonymous', '', '',
                      False, False, False)
            nc.changePassword(self.cfg.buildLabel, 'anonymous', 'anonymous')

    def testReferencesAndDescendants(self):
        client, userId = self.quickMintAdmin("testuser", "testpass")
        projectId = self.newProject(client, "testproject")

        v1 = "/testproject.%s@rpl:linux/1.0-1-1" % MINT_PROJECT_DOMAIN
        f1 = ''

        self.addComponent("trove:runtime", v1, f1)
        self.addCollection("trove", v1, [":runtime"], defaultFlavor = f1)

        # set up a collection that includes both
        v2 = "/testproject.%s@rpl:baz/1.0-1-1" % MINT_PROJECT_DOMAIN
        self.addCollection("group-dist", v2, [("trove", v1)], defaultFlavor = f1)

        # and set up a shadow
        v3 = "/testproject.%s@rpl:linux//prod/1.0-1-1" % MINT_PROJECT_DOMAIN
        self.addComponent("trove:runtime", v3, f1)
        self.addCollection("trove", v3, [":runtime"], defaultFlavor = f1)

        page = self.webLogin('testuser', 'testpass')
        page = self.fetch("/findRefs?trvName=trove;trvVersion=%s" % v1)

        self.failUnless(v3 in page.body)
        self.failUnless(("group-dist=%s" % v2) in page.body)

    def testVersions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        hostname = 'testproject.%s' % MINT_PROJECT_DOMAIN


        # copied straight from conary-test-1.1/clonetest.py --sgp
        os.chdir(self.workDir)
        self.newpkg("testcase")
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe1)
        self.addfile("testcase.recipe")
        self.commit()
        self.cookFromRepository('testcase')

        self.mkbranch("1.0-1", "%s@rpl:shadow" % hostname, "testcase:source",
                      shadow = True)

        os.chdir(self.workDir)
        shutil.rmtree("testcase")
        self.checkout("testcase", "%s@rpl:shadow" % hostname)
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe2)
        self.commit()

        self.cfg.buildLabel = versions.Label("%s@rpl:shadow" % hostname)
        self.cookFromRepository('testcase')
        self.cfg.buildLabel = versions.Label("%s@rpl:devel" % hostname)

        self.clone('/%s@rpl:devel' % hostname,
                   'testcase:source=%s@rpl:shadow' % hostname)
        self.clone('/%s@rpl:devel' % hostname,
                   'testcase=%s@rpl:shadow' % hostname,
                   fullRecurse=False)

        self.startMintServer()
        page = self.webLogin('testuser', 'testpass')
        self.assertContent('/repos/testproject/troveInfo?t=testcase', code = [200],
            content = '"%s@rpl:shadow": [["1.1-0.1-1", "troveInfo?t=testcase;v=/%s%%40rpl%%3Adevel' % (hostname, hostname),
            server = self.getProjectServerHostname())
        self.assertContent('/repos/testproject/troveInfo?t=testcase', code = [200],
            content = '"shadow"',
            server = self.getProjectServerHostname())

    def testShadowedFrom(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        hostname = 'testproject.%s' % MINT_PROJECT_DOMAIN

        os.chdir(self.workDir)
        self.newpkg("testcase")
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe1)
        self.addfile("testcase.recipe")
        self.commit()
        self.cookFromRepository('testcase')

        self.mkbranch("1.0-1", "%s@rpl:shadow" % hostname, "testcase:source",
                      shadow = True)
        os.chdir(self.workDir)
        shutil.rmtree("testcase")
        self.checkout("testcase", "%s@rpl:shadow" % hostname)
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe2)
        self.commit()
        self.cookFromRepository('testcase', versions.Label("%s@rpl:shadow" % hostname))
        self.clone('/%s@rpl:devel' % hostname,
                   'testcase:source=%s@rpl:shadow' % hostname)
        self.clone('/%s@rpl:devel' % hostname,
                   'testcase=%s@rpl:shadow' % hostname,
                   fullRecurse=False)
        self.cookFromRepository('testcase', versions.Label("%s@rpl:shadow" % hostname))
        self.mkbranch('/%s@rpl:devel//shadow/1.1-0.1' % hostname,  "%s@rpl:shadow2" % hostname, "testcase:source", shadow=True)
        self.cookFromRepository('testcase', versions.Label("%s@rpl:shadow2" % hostname))

        self.startMintServer()
        page = self.fetch('/repos/testproject/troveInfo?t=testcase')
        self.failIf('/%s@rpl:devel//shadow/1.1-0.1' % hostname not in page.body,
                    'First shadow not found.')
        self.failIf('/%s@rpl:devel/1.0-1' % hostname not in page.body,
                    'Second shadow not found.')
        self.failIf('Shadowed from' not in page.body,
                    'Trove does not appear shadowed')
            
    def testClonedFrom(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        hostname = 'testproject.%s' % MINT_PROJECT_DOMAIN

        # copied straight from conary-test-1.1/clonetest.py --sgp
        os.chdir(self.workDir)
        self.newpkg("testcase")
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe1)
        self.addfile("testcase.recipe")
        self.commit()
        self.cookFromRepository('testcase')

        self.mkbranch("1.0-1", "%s@rpl:shadow" % hostname, "testcase:source",
                      shadow = True)

        os.chdir(self.workDir)
        shutil.rmtree("testcase")
        self.checkout("testcase", "%s@rpl:shadow" % hostname)
        os.chdir("testcase")
        self.writeFile("testcase.recipe", testTransientRecipe2)
        self.commit()

        self.cfg.buildLabel = versions.Label("%s@rpl:shadow" % hostname)
        self.cookFromRepository('testcase')
        self.cfg.buildLabel = versions.Label("%s@rpl:devel" % hostname)

        self.clone('/%s@rpl:devel' % hostname,
                   'testcase:source=%s@rpl:shadow' % hostname)
        self.clone('/%s@rpl:devel' % hostname,
                   'testcase=%s@rpl:shadow' % hostname,
                   fullRecurse=False)

        self.startMintServer()
        page = self.webLogin('testuser', 'testpass')
        page = self.fetch("/repos/testproject/troveInfo?t=testcase")
        self.failUnless("Cloned from:" in page.body,
                "Missing cloned from information in repos browser")
        self.failUnless('/%s@rpl:devel//shadow/1.1-0.1-1' % hostname in page.body, "Wrong version displayed as clone")

        page = self.fetch("/repos/testproject/troveInfo?t=testcase:source")
        self.failUnless("Cloned from:" in page.body,
                "Missing cloned from information from source in repos browser")

    def testPGPAndPermForms(self):
        client, userId = self.quickMintAdmin('testuser', 'testpass')
        page = self.webLogin('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)
        v1 = "/testproject.%s@rpl:linux/1.0-1-1" % MINT_PROJECT_DOMAIN
        f1 = ''

        self.addComponent("trove:runtime", v1, f1)
        self.addCollection("trove", v1, [":runtime"], defaultFlavor = f1)
        self.setServer(self.getProjectServerHostname(), self.port)
        rep = self.startMintServer()
        # Load getOpenPGPKey page
        page = page.fetch("/repos/testproject/getOpenPGPKey?search=0ED565B9")
        self.failIf('OpenPGP Ke' not in page.body, 'Unable to retrieve PGP key')
        # Load pgpAdminForm
        page = page.fetch('/repos/testproject/pgpAdminForm')
        self.failIf('--Nobody--' not in page.body, 'Error PGP Admin Page.')
        # User List
        page = page.fetch('/repos/testproject/userlist')
        self.failIf('<B>rb_owner</B>' not in page.body, 'Error in user list')
        # addPermForm
        page = page.fetch('/repos/testproject/addPermForm')
        self.failIf('testuser' not in page.body, 'Error in addPermForm')
        # manageRoleForm
        page = page.fetch('/repos/testproject/manageRoleForm?roleName=rb_owner')
        self.failIf('"testuser"' not in page.body, 'Incorrect user list')
        self.failIf('Edit Role' not in page.body, 'Error in manageRoleForm')
        # addRoleForm
        page = page.fetch('/repos/testproject/addRoleForm')
        self.failIf('Add Role' not in page.body, 'Error in addRoleForm')
        # editPermForm
        page = page.fetch('/repos/testproject/editPermForm?role=testuser&writeperm=1&remove=1')
        self.failIf('Edit Permission' not in page.body, 'Error in editPermForm')

    def testPGPOperations(self):
        client, userId = self.quickMintAdmin('testuser', 'testpass')
        page = self.webLogin('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject', MINT_PROJECT_DOMAIN)

        # add archive/key.asc to project
        project = client.getProject(projectId)
        gpgData = file(os.path.join(pathManager.getPath('MINT_ARCHIVE_PATH'), 'key.asc'))

        from conary import conaryclient
        cclient = conaryclient.ConaryClient(project.getConaryConfig())
        cclient.getRepos().addNewAsciiPGPKey("testproject.%s@rpl:devel" % MINT_PROJECT_DOMAIN,
            'testuser', gpgData.read())
        gpgData.close()

        # make sure we see part of the whole key in the response
        self.setServer(self.getProjectServerHostname(), self.port)
        page = self.fetch("/repos/testproject/getOpenPGPKey?search=F94E405E")
        self.failUnless('mIsEQwCyngEEAJ3MC9HwzDve2JzvEdhS' in page.body)

    def testRepoPermissions(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        projectId = self.newProject(client, 'Foo', 'testproject',
                MINT_PROJECT_DOMAIN)

        self.fetch('/repos/testproject/getOpenPGPKey')
        self.fetch('/repos/testproject/pgpAdminForm')
        self.fetch('/repos/testproject/pgpChangeOwner?key=blah&owner=blah', ok_codes = [403])
        self.fetch('/repos/testproject/userlist', ok_codes = [403])
        self.fetch('/repos/testproject/deleteRole?roleName=foo', ok_codes=[403])
        self.fetch('/repos/testproject/addPermForm', ok_codes=[403])
        self.fetch('/repos/testproject/addPerm', ok_codes=[403])
        self.fetch('/repos/testproject/addRoleForm', ok_codes=[403])
        self.fetch('/repos/testproject/manageRoleForm?roleName=testuser', ok_codes=[403])
        self.fetch('/repos/testproject/manageRole', ok_codes=[403])
        self.fetch('/repos/testproject/addRole', ok_codes=[403])
        self.fetch('/repos/testproject/deletePerm', ok_codes=[403])
        self.fetch('/repos/testproject/editPermForm', ok_codes=[403])
        self.fetch('/repos/testproject/editPerm', ok_codes=[403])

        page = self.webLogin('testuser', 'testpass')
        page.fetch('/repos/testproject/getOpenPGPKey')
        page.fetch('/repos/testproject/pgpAdminForm')
        page.fetch('/repos/testproject/pgpChangeOwner?key=blah&owner=blah', ok_codes = [403])
        page.fetch('/repos/testproject/userlist')
        page.fetch('/repos/testproject/deleteRole')
        page.fetch('/repos/testproject/addPermForm')
        page.fetch('/repos/testproject/addPerm')
        page.fetch('/repos/testproject/addRoleForm')
        page.fetch('/repos/testproject/manageRoleForm?roleName=rb_user')
        page.fetch('/repos/testproject/manageRole')
        page.fetch('/repos/testproject/addRole')
        page.fetch('/repos/testproject/deletePerm')
        page.fetch('/repos/testproject/editPermForm')
        page.fetch('/repos/testproject/editPerm')

if __name__ == "__main__":
    testsuite.main()

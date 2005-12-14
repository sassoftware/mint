#!/usr/bin/python2.4
#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import mint_rephelp

from repostest import testRecipe
from conary import versions

class MintTest(mint_rephelp.WebRepositoryHelper):
    def testNoLocalRedirect(self):
        page = self.assertCode('', code = 200)

    def testLogin(self):
        self.quickMintUser('foouser','foopass')

        page = self.fetch('')
        if 'not logged in' not in page.body:
            self.fail("Login form did not appear on page")
        page = page.fetch('/processLogin', postdata = \
            {'username': 'foouser',
             'password': 'foopass'})
        if 'not logged in' in page.body:
            self.fail("Login form appeared on page for logged in user")

        page = page.assertCode('/logout', code = 301)
        page = self.fetch('')
        if 'not logged in' not in page.body:
            self.fail("Login form did not appear on page")
        page = page.fetch('/processLogin', postdata = \
            {'username': 'wronguser',
             'password': 'foopass'})

    def testLoginRedirect(self):
        # test to make sure that a login on one page
        # will redirect you back to that page after login
        self.quickMintUser('foouser', 'foopass')

        page = self.fetch('/search?type=Projects&search=abcd')
        startUrl = page.url

        page = page.postForm(0, self.post, {'username': 'foouser',
                                            'password': 'foopass'})
        assert(page.headers['Location'].endswith(startUrl))
        assert(page.code == 301)

    def testNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        # explicit redirect expected
        page = page.fetch('/createProject', postdata =
                          {'title': 'Test Project',
                           'hostname': 'test'})

        project = client.getProjectByHostname("test")
        assert(project.getName() == 'Test Project')

    def testEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/project/foo/editProject', code = 200)

    def testProcessEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        page = self.webLogin('foouser', 'foopass')
        page = page.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'Bar',
                           'branch' : 'foo:bar'},
                          ok_codes = [301])

        project = client.getProject(projectId)
        assert(project.name == 'Bar')
        assert(project.getLabel() == 'foo.rpath.local@foo:bar')

    def testEditProjectBranch(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        page = self.webLogin('foouser', 'foopass')

        # edit the project label to something not related to project fqdn
        cu = self.db.cursor()
        cu.execute("UPDATE Labels SET label=? WHERE projectId=?",
                   'bar.rpath.com@rpl:devel', projectId)

        page = page.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'foo',
                           'branch' : 'foo:bar'},
                           ok_codes = [301])

        project = client.getProject(projectId)
        assert(project.getLabel() == 'bar.rpath.com@foo:bar')

    def testBrowseProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        for sortOrder in range(10):
            page = self.fetch('/projects?sortOrder=%d' % sortOrder,
                               ok_codes = [200])

    def testSearchProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/search?type=Projects&search=foo',
                          ok_codes = [200])
        assert('match found for') in page.body

    def testSearchPackages(self):
        page = self.fetch('/search?type=Packages&search=%25%25%25',
                          ok_codes = [200])

    def testProjectsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/project/foo/', ok_codes = [200])

    def testMembersPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/project/foo/members/', ok_codes = [200])

    def testReleasesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.assertContent('/project/foo/releases/',
                                  ok_codes = [200],
                                  content = 'This project has no releases.')

    def testMailListsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/project/foo/mailingLists',
                                  ok_codes = [200])

    # FIXME: test can't be run until mint shims pages in the /repos stack.
    def testPgpAdminPage(self):
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/repos/foo/pgpAdminForm',
                                  ok_codes = [200])

    # FIXME: test can't be run until mint shims pages in the /repos stack.
    def testRepoBrowserPage(self):
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.assertContent('/repos/foo/browse',
                                  ok_codes = [200],
                                  content = 'Repository Browser')

    def testGroupBuilderInResources(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        # test for group builder while not logged in
        page = self.assertNotContent('/project/foo/', ok_codes = [200],
                                 content = "Group Builder")

        page = self.webLogin('foouser', 'foopass')
        page = self.assertContent('/project/foo/', ok_codes = [200],
                                 content = "Group Builder")

    def testUploadKeyPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.assertContent('/uploadKey', ok_codes = [200],
                                 content = "Permission Denied")

        page = self.webLogin('foouser', 'foopass')

        page = self.assertNotContent('/uploadKey', ok_codes = [200],
                                 content = "Permission Denied")

    def testUploadKey(self):
        keyFile = open(testsuite.archivePath + '/key.asc')
        keyData = keyFile.read()
        keyFile.close()
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/processKey', postdata =
                          {'projects' : ['foo'],
                           'keydata' : keyData})
        if 'error' in page.body:
            self.fail('Posting OpenPGP Key to project failed.')

    def testCreateGroup(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/createGroup', postdata =
                          { 'groupName' : 'foo',
                            'version'   : '1.0.0' })

        groupTrove = client.getGroupTrove(1)

        assert(groupTrove.recipeName == 'group-foo')

    def testAddGroupTroveItem(self):
        client, userId = self.quickMintUser('testuser','testpass')
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("test.rpath.local@rpl:devel"),
            ignoreDeps = True)

        page = self.webLogin('testuser', 'testpass')

        groupTrove = client.createGroupTrove(projectId, 'group-foo',
                                             '1.0.0', '', False)

        page = self.fetch('/project/test/editGroup?id=%d' % groupTrove.id,
                          ok_codes = [200])

        page = self.fetch('/project/test/addGroupTrove?id=%d&trove=testcase&projectName=test&referer=/' %
                          groupTrove.id)

        assert groupTrove.listTroves != []

    def testUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/userSettings',
                          ok_codes = [200])

    def testEditUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')

        user = client.getUser(userId)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/editUserSettings', postdata =
                          { 'fullName' : 'Bob Loblaw',
                            'email'    : user.email},
                          ok_codes = [301])

    def testNonExistProject(self):
        self.assertCode('/project/doesnotexist', code = 404)

    def testUnconfirmedAccess(self):
        # make a project for later then forget this user
        client, userId = self.quickMintUser('foouser','foopass')

        projectId = self.newProject(client, 'Foo', 'foo')
        cu = self.db.cursor()
        cu.execute("INSERT INTO Confirmations VALUES (?, ?, ?)", userId, 0, 40 * "0")
        page = self.webLogin('foouser', 'foopass')
        if "Email Confirmation Required" not in page.body:
            self.fail('Unconfirmed user broke out of confirm email jail'
                      ' on front page.')
        page = self.fetch('/project/foo/', ok_codes = [200])
        if "Email Confirmation Required" not in page.body:
            self.fail('Unconfirmed user broke out of confirm email jail'
                      ' on project home page.')
        page = self.fetch('/projects', ok_codes = [200])
        
        if "Email Confirmation Required" not in page.body:
            self.fail('Unconfirmed user broke out of confirm email jail'
                      ' on projects page.')

        # this can't be tested until shim works
        #page = self.fetch('/repos/stuff/browse', ok_codes = [200])
        #if "Email Confirmation Required" not in page.body:
        #    self.fail('Unconfirmed user broke out of confirm email jail'
        #              ' on repository page.')

        page = self.fetch('/editUserSettings', postdata = \
                          {'email'    : ''})
        if "Email Confirmation Required" in page.body:
            self.fail('Unconfirmed user was unable to change email address.')

        page = self.fetch('/logout', ok_codes = [301])

        if "Email Confirmation Required" in page.body:
            self.fail('Unconfirmed user was unable to log out.')

        page = self.fetch('/confirm?id=%s' % (40*"0"), ok_codes = [200])
        if "Your account has now been confirmed." not in page.body:
            self.fail('Unconfirmed user was unable to confirm.')

    def testSessionStability(self):
        newSid = '1234567890ABCDEF1234567890ABCDEF'
        client, userId = self.quickMintUser('foouser','foopass')
        # session not in table and not cached
        page = self.webLogin('foouser', 'foopass')

        # session in table and cached
        page = self.fetch('/', ok_codes = [200])

        self.failIf('Login' in page.body,
                    'Cached session appears to be logged out')

        # now move the session--effectively kill it, but we'll need it again
        cu = self.db.cursor()
        cu.execute("UPDATE Sessions SET sessIdx=sessIdx + 1, sid=?",
                   newSid)

        #session not in table but is cached
        page = self.fetch('/projects?sortOrder=9', ok_codes = [200])

        # session not in table and not in cache
        self.failIf('Login' not in page.body,
                    'Unchached session not logged out')

        # HACK alter cookie to match what we moved session to earlier
        self.cookies['.rpath.local']['/']['pysid'].coded_value = newSid
        # session in db but not in cache
        cookie = 'pysid'
        self.registerExpectedCookie(cookie)
        page = self.fetch('/', ok_codes = [200])
        self.failIf('Login' in page.body,
                    'Uncached session appears to be logged out')

if __name__ == "__main__":
    testsuite.main()

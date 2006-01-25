#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import mint_rephelp

from repostest import testRecipe
from conary import versions
import cPickle

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def sessionData(self):
        sid = self.cookies['.rpath.local']['/']['pysid'].value
        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)
        return cPickle.loads(cu.fetchone()[0])['_data']

    def testNoLocalRedirect(self):
        page = self.assertCode('', code = 200)

    def testLogin(self):
        self.quickMintUser('foouser','foopass')

        page = self.fetch('')

        if '/processLogin' not in page.body:
            self.fail("Login form did not appear on page")
        page = page.fetch('/processLogin', postdata = \
            {'username': 'foouser',
             'password': 'foopass'})
        if '/processLogin' in page.body:
            self.fail("Login form appeared on page for logged in user")

        page = page.assertCode('/logout', code = 301)
        page = self.fetch('')
        if '/processLogin' not in page.body:
            self.fail("Login form did not appear on page")
        page = page.fetch('/processLogin', postdata = \
            {'username': 'wronguser',
             'password': 'foopass'})

    def testRegistration(self):
        cu = self.db.cursor()
        cu.execute("SELECT confirmation FROM Confirmations")
        assert(not cu.fetchall())

        page = self.assertCode('/register', code = 200)

        page = page.postForm(1, self.post, {'username':  'foouser',
                                            'password':  'foopass',
                                            'password2': 'foopass',
                                            'email':     'foo@localhost',
                                            'email2':     'foo@localhost',
                                            'tos':       'True',
                                            'privacy':   'True'})

        cu.execute("SELECT confirmation FROM Confirmations")
        conf = cu.fetchall()[0][0]

        page = self.assertCode("/confirm?id=%s" % conf, code = 200)

        self.failIf("Your account has now been confirmed." not in page.body,
                    "Confirmation Failed")

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
        self.db.commit()

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

        assert('Search Results:') in page.body

    def testSearchPackages(self):
        page = self.fetch('/search?type=Packages&search=%25%25%25',
                          ok_codes = [200])

        assert('Search Results:') in page.body

    def testProjectsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/project/foo/', ok_codes = [200])

    def testMembersPage(self):
        self.quickMintUser('testuser','testpass')
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        self.webLogin('foouser', 'foopass')
        page = self.fetch('/project/foo/members/', ok_codes = [200])
        page = page.postForm(1, self.post, {'username' : 'testuser',
                                            'level' : 0})


    def testReleasesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.assertContent('/project/foo/releases/',
                                  ok_codes = [200],
                                  content = 'This project has no published releases.')

    def testMailListsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/project/foo/mailingLists',
                                  ok_codes = [200])

    def testPgpAdminPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        page = self.webLogin('foouser', 'foopass')

        page = page.fetch('/repos/foo/pgpAdminForm',
                                  ok_codes = [200])

    def testRepoBrowserPage(self):
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


    def testCreateGroup2(self):
        # this test fails due to a logical error in web unit.
        # the basic issue is a mixing of hidden and checkbox fields on the page
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/newGroup')

        page.postForm(1, self.post, {'groupName' : 'bar', 'version' : '1.1'})

    def testPickArch(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        group = client.createGroupTrove(projectId, 'group-foo', '1.0.0',
                                        'no desc', False)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/pickArch?id=1')

        # this line would trigger a group cook if a job server were running
        page.postForm(2, self.post, {'arch' : "1#x86", 'id' : '1'})

    def testDeletedGroup(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/createGroup', postdata =
                          { 'groupName' : 'foo',
                            'version'   : '1.0.0' })
        page = page.fetch('/project/foo/editGroup?id=1')

        s = self.sessionData()
        cu = self.db.cursor()
        cu.execute("DELETE FROM GroupTroves WHERE groupTroveId=?", s['groupTroveId'])
        self.db.commit()

        page.assertContent('/project/foo/groups', ok_codes = [200],
            content = 'You can use Group Builder to create a group')

    def testAddGroupTroveItem(self):
        client, userId = self.quickMintUser('testuser','testpass')
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject.rpath.local@rpl:devel"),
            ignoreDeps = True)

        page = self.webLogin('testuser', 'testpass')

        groupTrove = client.createGroupTrove(projectId, 'group-foo',
                                             '1.0.0', '', False)

        page = self.fetch('/project/testproject/editGroup?id=%d' % groupTrove.id,
                          ok_codes = [200])

        page = self.fetch('/project/testproject/addGroupTrove?id=%d&trove=testcase&projectName=testproject&referer=/' %
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
        cu.execute("INSERT INTO Confirmations VALUES (?, ?, ?)", userId, 0,
                   40 * "0")
        self.db.commit()
        page = self.webLogin('foouser', 'foopass')
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail'
                    ' on front page.')
        page = self.fetch('/project/foo/', ok_codes = [200])
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail'
                    ' on project home page.')
        page = self.fetch('/projects', ok_codes = [200])

        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail on'
                    ' projects page.')

        page = self.fetch('/repos/stuff/browse', ok_codes = [200])
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail on'
                    ' repository page.')

        page = self.fetch('/editUserSettings', postdata = \
                          {'email'    : ''})
        self.failIf("Email Confirmation Required" in page.body,
                    'Unconfirmed user was unable to change email address.')

        page = self.fetch('/logout', ok_codes = [301])

        self.failIf("Email Confirmation Required" in page.body,
                    'Unconfirmed user was unable to log out.')

        page = self.fetch('/confirm?id=%s' % (40*"0"), ok_codes = [200])
        self.failIf("Your account has now been confirmed." not in page.body,
                    'Unconfirmed user was unable to confirm.')

    def testSessionStability(self):
        newSid = '1234567890ABCDEF1234567890ABCDEF'
        client, userId = self.quickMintUser('foouser','foopass')
        # session not in table and not cached
        page = self.webLogin('foouser', 'foopass')

        # session in table and cached
        page = self.fetch('/', ok_codes = [200])

        self.failIf('You are signed in' not in page.body,
                    'Cached session appears to be logged out')

        # now move the session--effectively kill it, but we'll need it again
        cu = self.db.cursor()
        cu.execute("UPDATE Sessions SET sessIdx=sessIdx + 1, sid=?",
                   newSid)
        self.db.commit()

        #session not in table but is cached
        page = self.fetch('/projects?sortOrder=9', ok_codes = [200])

        # session not in table and not in cache
        self.failIf('You are signed in' in page.body,
                    'Unchached session not logged out')

        # HACK alter cookie to match what we moved session to earlier
        self.cookies['.rpath.local']['/']['pysid'].coded_value = newSid
        # session in db but not in cache
        cookie = 'pysid'
        self.registerExpectedCookie(cookie)
        page = self.fetch('/', ok_codes = [200])
        self.failIf('You are signed in' not in page.body,
                    'Uncached session appears to be logged out')

    def testUnknownError(self):
        page = self.assertContent('/unknownError', ok_codes = [200],
            content = 'An unknown error occured')

    def testDownloadISO(self):
        filename = self.tmpDir + "/test.iso"
        data = "Hello World"
        f = file(filename, "w")
        f.write(data)
        f.close()

        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", "rpath.org")
        release = client.newRelease(projectId, "Test Release")
        release.setImageTypes([0])
        release.setPublished(True)

        cu = self.db.cursor()
        cu.execute("INSERT INTO ImageFiles VALUES (1, ?, 0, ?, 'Test Image')", release.id, filename)
        self.db.commit()

        page = self.fetch('/downloadImage/1/test.iso')
        assert(page.body == data)

    def testUtf8ProjectName(self):
        raise testsuite.SkipTestException, "need to figure out how to exactly emulate someone entering utf-8 into a web form"
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')
        project = client.getProject(projectId)

        project.editProject("http://example.com/",
            "This project has \u266a extended characters in its description!", "Foo Title")
        project.refresh()

        page = self.assertContent('/project/foo/', ok_codes = [200],
            content = project.getDesc())


if __name__ == "__main__":
    testsuite.main()

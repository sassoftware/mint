#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import cPickle
import os
import urlparse

import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN, MINT_DOMAIN
import rephelp

from mint import mint_error
from mint import database
from mint import buildtypes
from mint import jobstatus
from mint.distro import jsversion

from repostest import testRecipe

from conary import versions
from conary.repository import errors

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def sessionData(self):
        sid = self.cookies['%s.%s' % (self.mintCfg.hostName,
                MINT_PROJECT_DOMAIN)]['/']['pysid'].value
        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)
        return cPickle.loads(cu.fetchone()[0])['_data']

    def testNoLocalRedirect(self):
        page = self.assertCode('', code = 200)

    def testRedirect(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        self.setOptIns('foouser')
        projectId = self.newProject(client)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # pick a page to log in from
        pageURI = '/project/testproject/builds'
        page = self.fetch(pageURI)

        page = page.postForm(1, self.fetchWithRedirect,
                {'username':'foouser', 'password':'foopass'})

        self.failIf(pageURI not in page.url,
                    "rBO explicit redirects are improper. "
                    "Web browsers will be confused.")

    def testLogin(self):
        self.quickMintUser('foouser','foopass')

        # historically, port was missing from login form action
        port = self.mintCfg.SSL and self.securePort or self.port
        page = self.assertContent('/', '%d/processLogin' % port)

        self.webLogin('foouser', 'foopass')

        page = self.fetch(self.mintCfg.basePath)
        page = page.fetchWithRedirect('/logout')

        if '/processLogin' not in page.body:
            self.fail("Login form did not appear on page")

    def testLoginBlockCookie(self):
        self.quickMintUser('foouser', 'foopass')

        self.accept_cookies = False
        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'foouser', 'password': 'foopass'})
        self.failIf('You cannot log in' not in page.body,
                    "Browser blocked cookies and didn't go to error page.")

    def testLoginBlockOneCookie(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        siteUrl = 'http://' + self.mintCfg.siteHost + self.mintCfg.basePath
        projectUrl = 'http://' +  mint_rephelp.MINT_HOST + '.' + \
                      mint_rephelp.MINT_PROJECT_DOMAIN + ":" + str(self.port) \
                      + self.mintCfg.basePath

        siteHost = mint_rephelp.MINT_HOST + '.' + mint_rephelp.MINT_DOMAIN
        projectHost = mint_rephelp.MINT_HOST + '.' + \
                      mint_rephelp.MINT_PROJECT_DOMAIN

        for url in (siteUrl, projectUrl):
            for host in (siteHost, projectHost):
                self.cookies.clear()
                page = self.fetchWithRedirect(url)

                page = page.postForm(1, self.fetch,
                                     {'username': 'foouser',
                                      'password': 'foopass'})

                depth = 0
                while page.code in (301, 302):
                    assert (depth < 20), 'Max Depth Exceeded'
                    if host in self.cookies:
                        # delete only one of two cookies.
                        del self.cookies[host]
                    page = self.fetch( \
                        urlparse.urljoin(url, page.headers['Location']))
                    depth += 1

                self.failIf('You cannot log in' not in page.body,
                            "user hit %s and deleted cookie: %s, but "
                            "didn't trigger error" % (url, host))

                # ensure project page is not logged in (project domain cookie)
                self.assertNotContent("%sproject/%s" % (self.mintCfg.basePath, project.hostname), '/logout')
                # ensure front page is not logged in. (site domain cookie)
                self.assertNotContent(self.mintCfg.basePath, '/logout')

    def testLoginWrongUser(self):
        page = self.fetch('/')

        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'baduser', 'password': 'somepassword'})

        if 'Error' not in page.body:
            self.fail("Wrong username should show an error page.")

    def testLoginWrongPassword(self):
        self.quickMintUser('foouser','foopass')

        page = self.fetch('/')

        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'foouser', 'password': 'badpassword'})

        if 'Error' not in page.body:
            self.fail("Wrong password should show an error page.")

    def testLoginCookies(self):
        self.quickMintUser('foouser', 'foopass')

        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'foouser', 'password': 'foopass'})

        page = page.fetch('/')
        page.registerExpectedCookie('pysid')

        self.failUnless('%s.%s' % (self.mintCfg.hostName, MINT_DOMAIN) \
                in self.cookies.keys(),
                "%s missing from cookies" % MINT_DOMAIN)
        if (MINT_PROJECT_DOMAIN != MINT_DOMAIN):
            self.failUnless('%s.%s' % (self.mintCfg.hostName,
                MINT_PROJECT_DOMAIN) in self.cookies.keys(),
                "%s missing from cookies" % MINT_PROJECT_DOMAIN)
            self.assertEqual(self.cookies['%s.%s' % (self.mintCfg.hostName,
                MINT_DOMAIN)], self.cookies['%s.%s' % (self.mintCfg.hostName,
                MINT_PROJECT_DOMAIN)], "Cookies should be identical")

    def testLoginNonvolatileSession(self):
        self.quickMintUser('foouser','foopass')

        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'foouser', 'password': 'foopass'})

        self.failIf(self.cookies.values()[0]['/']['pysid']['expires'],
                "Session cookie has unexpected expiration")

        page.registerExpectedCookie('pysid')

        page = page.fetchWithRedirect('/logout')

        page = page.fetchWithRedirect('/')

        page = page.postForm(1, self.fetchWithRedirect,
                {'username'   : 'foouser',
                 'password'   : 'foopass',
                 'rememberMe' : '1'})

        for c in self.cookies.items():
            self.failUnless(c[1]['/']['pysid']['expires'],
                "Session cookie for %s is missing expiration" % c[0])

    def testLogout(self):
        client, userid = self.quickMintUser('foouser', 'foopass')
        self.setOptIns('foouser')
        self.newProject(client, 'Foo', 'foo')

        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username'   : 'foouser',
                 'password'   : 'foopass',
                 'rememberMe' : '1'})

        page.assertContent('/', '/logout')

        page = page.fetchWithRedirect('/logout')

        page = page.fetchWithRedirect('/project/foo', code = [200])
        self.failIf(('/logout' in page.body), "Still logged in on" \
                "project domain (cookie still active)")

        page = page.fetchWithRedirect('/', code = [200])
        self.failIf(('/logout' in page.body), "Still logged in on" \
                "main site domain (cookie still active)")

    def testLogoutNoCookie(self):
        self.quickMintUser('foouser', 'foopass')
        self.setOptIns('foouser')

        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username'   : 'foouser',
                 'password'   : 'foopass',
                 'rememberMe' : '1'})

        page.assertContent('/', '/logout')

        page = page.fetchWithRedirect('/logout')

        page = page.fetchWithRedirect('/')
        self.failIf('Set-Cookie:' in page.headers,
                "Cookies should not be set in headers after logout")

    def testLogoutWithNoSession(self):
        self.quickMintUser('foouser', 'foopass')

        page = self.fetch('/')
        page = page.fetchWithRedirect('/logout')

        self.failUnless('processLogin' in page.body,
                "Should have redirected to the front page.")

    def testCookieBeforeLogin(self):
        page = self.fetchWithRedirect('/')
        self.failIf('Set-Cookie:' in page.headers,
                "Cookies should not be set in headers before login")

    def testSessionCleanup(self):
        client, userId = self.quickMintUser('foouser','foopass')

        page = self.fetch('/')
        page = page.postForm(1, self.post, {'username'   : 'foouser',
                                            'password'   : 'foopass',
                                            'rememberMe' : '1'})

        sid = self.cookies.values()[0]['/']['pysid'].value

        cu = self.db.cursor()
        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)
        data = cPickle.loads(cu.fetchall()[0][0])

        # make session 2 days older than it was. this bypasses the need
        # to load the time module.
        data['_accessed'] = data['_accessed'] - 172800

        cu.execute("UPDATE Sessions SET data=? WHERE sid=?",
                   cPickle.dumps(data), sid)
        self.db.commit()

        client.server._server.cleanupSessions()

        cu.execute("SELECT data FROM Sessions WHERE sid=?", sid)

        self.failIf(not cu.fetchall(),
                    "A remembered session was destroyed during cleanup")

    def testRegistration(self):
        cu = self.db.cursor()
        cu.execute("SELECT confirmation FROM Confirmations")
        assert(not cu.fetchall())

        page = self.fetchWithRedirect('/register')
        page = page.postForm(1, page.post,
                {'newUsername':  'foouser',
                 'password':  'foopass',
                 'password2': 'foopass',
                 'email':     'foo@localhost',
                 'email2':    'foo@localhost',
                 'tos':       'True',
                 'privacy':   'True'})
        client = self.openMintClient()

        conf = client.server._server.getConfirmation('foouser')
        self.failIf(not conf, "Registration didn't add confirmation entry")

        page = self.assertCode("/confirm?id=%s" % conf, code = 200)

        self.failIf("Your account has now been confirmed." not in page.body,
                    "Confirmation Failed")

    def testLoginRedirect(self):
        # test to make sure that a login on one page
        # will redirect you back to that page after login
        client, userId = self.quickMintUser('foouser', 'foopass')
        self.setOptIns('foouser')

        self.newProject(client)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/testproject/')
        startUrl = page.url

        page = page.postForm(1, self.fetchWithRedirect, 
                {'username': 'foouser', 'password': 'foopass'})
        assert(page.url.endswith(startUrl))

    def testNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        page = page.postForm(1, self.fetchWithRedirect,
                {'title': 'Test Project', 'hostname': 'test'})

        project = client.getProjectByHostname("test")
        assert(project.getName() == 'Test Project')

    def testEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertCode('/project/foo/editProject', code = 200)

    def testProcessEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'Bar',
                           'branch' : 'foo:bar'},
                          ok_codes = [301])

        project = client.getProject(projectId)
        assert(project.name == 'Bar')
        assert(project.getLabel() == 'foo.' + MINT_PROJECT_DOMAIN + '@foo:bar')

    def testEditProjectBranch(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        page = self.webLogin('foouser', 'foopass')

        # edit the project label to something not related to project fqdn
        cu = self.db.cursor()
        cu.execute("UPDATE Labels SET label=? WHERE projectId=?",
                   'bar.rpath.com@rpl:devel', projectId)
        self.db.commit()

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'foo',
                           'branch' : 'foo:bar'})

        project = client.getProject(projectId)
        assert(project.getLabel() == 'bar.rpath.com@foo:bar')

    def testBrowseProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        for sortOrder in range(10):
            page = self.fetch('/projects?sortOrder=%d' % sortOrder,
                               ok_codes = [200])

    def testSearchProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.fetch('/search?type=Projects&search=foo',
                          ok_codes = [200])

        assert('Search Results:') in page.body

    def testSearchPackages(self):
        page = self.fetch('/search?type=Packages&search=%25%25%25',
                          ok_codes = [200])

        assert('Search Results:') in page.body

    def testProjectsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/', 
                ok_codes = [200])

    def testMembersPage(self):
        self.quickMintUser('testuser','testpass')
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/members/', 
                ok_codes = [200])
        page = page.postForm(1, self.post, {'username' : 'testuser',
                                            'level' : 0})


    def testBuildsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/builds/',
                                  content = 'has no published',
                                  code = [200])

    def testMailListsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/mailingLists',
                                  ok_codes = [200])

    def testPgpAdminPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        page = self.webLogin('foouser', 'foopass')

        page = page.fetchWithRedirect('/repos/testproject/pgpAdminForm',
            server = self.getProjectServerHostname())

    def testPgpAdminLink(self):
        # Ideally this test will change in the future. all users of the site
        # should be able to view public keys.
        from mint import userlevels
        client, userId = self.quickMintUser('foouser','foopass')
        devClient, userId = self.quickMintUser('devuser','devpass')
        nonClient, userId = self.quickMintUser('nonuser','nonpass')
        watcherClient, userId = self.quickMintUser('watchuser','watchpass')
        adminClient, userId = self.quickMintAdmin('adminuser','adminpass')

        projectId = self.newProject(client)
        project = client.getProject(projectId)

        project.addMemberByName('devuser', userlevels.DEVELOPER)
        project = watcherClient.getProject(projectId)
        project.addMemberByName('watchuser', userlevels.USER)

        # view shows up for owner
        self.webLogin('foouser', 'foopass')
        page = self.assertContent('/project/testproject/members',
                                  "View OpenPGP Signing Keys",
                                  server = self.getProjectServerHostname())
        page.fetchWithRedirect("/logout")

        # view shows up for developer
        self.webLogin('devuser', 'devpass')
        page = self.assertContent('/project/testproject/members',
                                  "View OpenPGP Signing Keys",
                                  server = self.getProjectServerHostname())
        page.fetchWithRedirect("/logout")

        # view doesn't show up for watcher
        self.webLogin('watchuser', 'watchpass')
        page = self.assertNotContent('/project/testproject/members',
                                  "View OpenPGP Signing Keys",
                                  server = self.getProjectServerHostname())
        page.fetchWithRedirect("/logout")

        # view doesn't show up for non-member
        self.webLogin('nonuser', 'nonpass')
        page = self.assertNotContent('/project/testproject/members',
                                  "View OpenPGP Signing Keys",
                                  server = self.getProjectServerHostname())
        page.fetchWithRedirect("/logout")

        # manage shows up for admin
        self.webLogin('adminuser', 'adminpass')
        page = self.assertContent('/project/testproject/members',
                                  "Manage OpenPGP Signing Keys",
                                  server = self.getProjectServerHostname())
        page.fetchWithRedirect("/logout")

    def testRepoBrowserPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/repos/foo/browse',
                                  code = [200],
                                  content = 'Repository Browser')

    def testGroupBuilderInResources(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        # test for group builder while not logged in
        page = self.assertNotContent('/project/foo/', code = [200],
                                 content = "Group Builder",
                                 server = self.getProjectServerHostname())

        page = self.webLogin('foouser', 'foopass')
        page = self.assertContent('/project/foo/', code = [200],
                                 content = "Group Builder",
                                 server = self.getProjectServerHostname())

    def testUploadKeyPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.assertContent('/uploadKey', code = [200],
                                 content = "Permission Denied")

        page = self.webLogin('foouser', 'foopass')

        page = self.assertNotContent('/uploadKey', code = [200],
                                 content = "Permission Denied")

    def testUploadKey(self):
        keyFile = open(testsuite.archivePath + '/key.asc')
        keyData = keyFile.read()
        keyFile.close()
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/processKey', postdata =
                          {'projects' : ['foo'],
                           'keydata' : keyData})
        if 'error' in page.body:
            self.fail('Posting OpenPGP Key to project failed.')

    def testCreateGroup(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/createGroup', postdata =
                          { 'groupName' : 'foo',
                            'version'   : '1.0.0' },
                            server = self.getProjectServerHostname())

        groupTrove = client.getGroupTrove(1)

        assert(groupTrove.recipeName == 'group-foo')


    def testCreateGroup2(self):
        # this test fails due to a logical error in web unit.
        # the basic issue is a mixing of hidden and checkbox fields on the page
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/project/foo/newGroup',
                server = self.getProjectServerHostname())

        page.postForm(1, self.post, {'groupName' : 'bar', 'version' : '1.1'})

    def testPickArch(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        group = client.createGroupTrove(projectId, 'group-foo', '1.0.0',
                                        'no desc', False)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/pickArch?id=1')

        # this line would trigger a group cook if a job server were running
        page.postForm(1, self.post, {'arch' : "1#x86", 'id' : '1'})

    def testDeletedGroup(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/createGroup', postdata =
                          { 'groupName' : 'foo',
                            'version'   : '1.0.0' })
        page = page.fetch('/project/foo/editGroup?id=1')

        s = self.sessionData()
        cu = self.db.cursor()
        cu.execute("DELETE FROM GroupTroves WHERE groupTroveId=?", s['groupTroveId'])
        self.db.commit()

        page.assertContent('/project/foo/groups', code = [200],
            content = 'You can use Group Builder to create a group')

    def testAddGroupTroveItem(self):
        client, userId = self.quickMintUser('testuser','testpass')
        projectId = self.newProject(client)

        self.makeSourceTrove("testcase", testRecipe)
        self.cookFromRepository("testcase",
            versions.Label("testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel"),
            ignoreDeps = True)

        page = self.webLogin('testuser', 'testpass')

        groupTrove = client.createGroupTrove(projectId, 'group-foo',
                                             '1.0.0', '', False)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/testproject/editGroup?id=%d' % groupTrove.id,
                          ok_codes = [200])

        page = self.fetch('/project/testproject/addGroupTrove?id=%d&trove=testcase&projectName=testproject&referer=/' %
                          groupTrove.id)

        assert groupTrove.listTroves != []

    def testUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')

        page = self.webLogin('foouser', 'foopass')

        page = self.fetchWithRedirect('/userSettings')

    def testEditUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')

        user = client.getUser(userId)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.post,
                          { 'fullName' : 'Bob Loblaw',
                            'email'    : user.email })

        user = client.getUser(userId)
        self.assertEqual(user.fullName, 'Bob Loblaw')

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

        page = self.fetch('/')
        page = page.postForm(1, self.fetchWithRedirect,
                {'username': 'foouser', 'password': 'foopass'})
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail'
                    ' on front page.')

        page = page.fetchWithRedirect('/project/foo/',
                server = self.getProjectServerHostname())
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail'
                    ' on project home page.')

        page = page.fetchWithRedirect('/projects',
                server = self.getProjectServerHostname())
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail on'
                    ' projects page.')

        page = page.fetchWithRedirect('/repos/foo/browse',
                server = self.getProjectServerHostname())
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail on'
                    ' repository page.')

        page = page.fetchWithRedirect('/editUserSettings', params = \
                          {'email'    : ''},
                          server = self.getProjectServerHostname())
        self.failIf("Email Confirmation Required" in page.body,
                    'Unconfirmed user was unable to change email address.')

        page = page.fetchWithRedirect('/logout')
        self.failIf("Email Confirmation Required" in page.body,
                    'Unconfirmed user was unable to log out.')

        page = self.fetchWithRedirect('/confirm?id=%s' % (40*"0"))
        self.failIf("Your account has now been confirmed." not in page.body,
                    'Unconfirmed user was unable to confirm.')

    def testSessionStability(self):
        newSid = '1234567890ABCDEF1234567890ABCDEF'
        username = 'foouser'
        client, userId = self.quickMintUser(username, 'foopass')
        # session not in table and not cached
        page = self.webLogin(username, 'foopass')

        # session in table and cached
        page = self.fetch('/', ok_codes = [200])

        self.failIf(username not in page.body,
                    'Cached session appears to be logged out')

        # now move the session--effectively kill it, but we'll need it again
        cu = self.db.cursor()
        cu.execute("UPDATE Sessions SET sessIdx=sessIdx + 1, sid=?",
                   newSid)
        self.db.commit()

        #session not in table but is cached
        page = self.fetch('/projects?sortOrder=9', ok_codes = [200])

        # session not in table and not in cache
        self.failIf(username in page.body,
                    'Uncached session not logged out')

        # HACK alter cookie to match what we moved session to earlier
        self.cookies['%s.%s' % (self.mintCfg.hostName, MINT_DOMAIN)]['/']['pysid'].coded_value = newSid

        # session in db but not in cache
        cookie = 'pysid'
        self.registerExpectedCookie(cookie)
        page = self.fetch('/', ok_codes = [200])
        self.failIf(username not in page.body,
                    'Uncached session appears to be logged out')

    def testUnknownError(self):
        page = self.assertContent('/unknownError', code = [200],
            content = 'An unknown error occured',
            server = self.getProjectServerHostname())

    def testDownloadISO(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)

        cu = self.db.cursor()
        cu.execute("INSERT INTO BuildFiles VALUES (1, ?, 0, 'test.iso', 'Test Image')",
                   build.id)
        self.db.commit()

        # check for the meta refresh tag
        page = self.assertCode('/downloadImage/1/test.iso', code = 301)

    def testUtf8ProjectName(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)

        project.editProject("http://example.com/",
            "This project has \xe2\x99\xaa \xe2\x99\xac extended characters in its description!",
            "Test Title")
        project.refresh()

        page = self.assertContent('/project/foo/', code = [200],
            content = project.getDesc(),
            server = self.getProjectServerHostname())


    def testGroupBuilderCloseBox(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)
        project = client.getProject(projectId)

        groupTrove = self.createTestGroupTrove(client, projectId)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        groupTrove = self.createTestGroupTrove(client, projectId)
        page = self.fetch('/project/testproject/editGroup?id=%d' % \
                          groupTrove.id)

        # go to a different page that so that the group box can show up
        page = self.assertContent('/project/testproject/builds',
                                  content = 'closeCurrentGroup')

        # then simulate clicking the close box to prove it closes properly
        page = self.assertNotContent("/project/testproject/closeCurrentGroup",
                                     content = 'closeCurrentGroup')

    def testGroupBuilderCook(self):
        # prove that the group builder box actually closes after cook
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # XXX: workaround to solve nesting XML-RPC call in cookGroup
        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        groupTrove = self.createTestGroupTrove(client, projectId)

        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])

        groupTrove.addTrove('test', '/testproject.' + MINT_PROJECT_DOMAIN + \
                            '@rpl:devel/1.0-1',
                            '', '', False, False, False)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # editing the group makes the Pane active
        page = self.fetch('/project/testproject/editGroup?id=%d' % \
                          groupTrove.id)

        # cook the group to make it go away
        page = self.fetch('/project/testproject/pickArch?id=%d' % \
                          groupTrove.id)

        page = page.postForm(1, self.post, {'flavor': ['1#x86']})

        page = self.assertNotContent('/project/testproject/builds',
                              content = 'closeCurrentGroup')

    def testGroupCookRespawn(self):
        # prove that the group builder box actually closes after cook
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # XXX: workaround to solve nesting XML-RPC call in cookGroup
        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        groupTrove = self.createTestGroupTrove(client, projectId)

        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])

        groupTrove.addTrove('test', '/testproject.' + MINT_PROJECT_DOMAIN + \
                            '@rpl:devel/1.0-1',
                            '', '', False, False, False)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # editing the group makes the Pane active
        page = self.fetch('/project/testproject/editGroup?id=%d' % \
                          groupTrove.id)

        # cook the group to make it go away
        page = self.fetch('/project/testproject/pickArch?id=%d' % \
                          groupTrove.id)

        page.postForm(1, self.post, {"flavor" : ["1#x86"]})

        cu = self.db.cursor()
        cu.execute("UPDATE Jobs SET status=?, statusMessage='Finished'",
                   jobstatus.FINISHED)
        self.db.commit()

        page = page.postForm(1, self.post, {"flavor" : ["1#x86"]})

        self.failIf('Error' in page.body,
                    "recooking triggered backtrace")

    def testGroupTroveItem(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        groupTrove = self.createTestGroupTrove(client, projectId)

        repos = self.openRepository()

        self.addQuickTestComponent('foo:data',
                                   '/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/1.0-1',
                                   repos = repos)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/testproject/editGroup?id=%d' % \
                          groupTrove.id)

        page = self.fetch('/project/testproject/addGroupTrove?id=%d;' % \
                          groupTrove.id + \
                          'trove=foo:data;projectName=testproject&referer=/')

        # ensure the trove was added to the group builder box
        page = self.assertContent('/project/testproject', 'foo:data')

    def testProjectReg(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # link historically showed up wrong by not pre-pending a /
        page = self.assertNotContent('/project/testproject/',
                                     'a href="register"')

    def testReposSignin(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # link historically brought up a spurious "my projects" pane
        page = self.assertContent('/repos/testproject/browse',
                                     '/processLogin',
                                     server = self.getProjectServerHostname())

        page = self.webLogin('foouser', 'foopass')

        page = self.assertContent('/repos/testproject/browse',
                                     '/newProject',
                                     server = self.getProjectServerHostname())

    def testTroveInfoLogin(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        self.addQuickTestComponent('foo:data',
            '/testproject.' + MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1')

        # link historically brought up a spurious "my projects" pane
        page = self.assertContent( \
            '/repos/testproject/troveInfo?t=foo:data',
            '/processLogin',
            server = self.getProjectServerHostname())

        page = self.webLogin('foouser', 'foopass')

        page = self.assertContent( \
            '/repos/testproject/troveInfo?t=foo:data',
            '/newProject',
            server = self.getProjectServerHostname())

    def testMailSignin(self):
        raise testsuite.SkipTestException

        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # link historically brought up a spurious "my projects" pane
        page = self.assertContent('/project/testproject/mailingLists',
                                     '/processLogin',
                                     server = self.getProjectServerHostname())

        page = self.webLogin('foouser', 'foopass')

        page = self.assertContent('/project/testproject/mailingLists',
                                     '/newProject',
                                     server = self.getProjectServerHostname())

    def testMailSubscribe(self):
        raise testsuite.SkipTestException

        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # historically, there was an extra slash in subscribe links
        page = self.assertNotContent('/project/testproject/mailingLists',
                                     '/project/testproject//')

        page = self.fetch('/project/testproject/subscribe?list=testproject')

        # and test clicking subscribe a second time.
        page = self.assertNotContent( \
            '/project/testproject/subscribe?list=testproject', 'error')

    def testGrpTrvSource(self):
        client, userId = self. quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        repos = self.openRepository()

        self.addQuickTestComponent('foo:source',
                                   '/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/1.0-1',
                                   repos = repos)

        groupTrove = client.createGroupTrove(projectId, 'group-foo', '1.0.0',
                                             'no desc', False)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # activate the group trove builder
        page = self.fetch('/project/testproject/editGroup?id=%d' % \
                          groupTrove.id)

        # source troves can show up on browse page if there's no binary with it
        page = self.assertNotContent("/repos/testproject/browse?char=F",
                                     "Add to group-foo")


        # now add a trove that should show up for troveInfo. this couldn't
        # be added sooner or it would confuse browsing check
        self.addQuickTestComponent('foo:data',
                                   '/testproject.' + MINT_PROJECT_DOMAIN + \
                                   '@rpl:devel/1.0-1', repos = repos)


        # XXX: workaround to solve nesting XML-RPC call in cookGroup
        project = client.getProject(projectId)
        self.moveToServer(project, 1)

        # check troveinfo page for proper source component rules
        page = self.assertNotContent( \
            '/repos/testproject/troveInfo?t=foo:source',
            'Add to group-foo')

        page = self.assertContent( \
            '/repos/testproject/troveInfo?t=foo:data',
            'Add to group-foo')

    def testDocJail(self):
        # ensure the legal pages implement a jail for documents. 404 on error
        page = self.fetch("/legal?page=SOMETHING_NOT_THERE", ok_codes = [404])
        page = self.fetch('/legal')
        refPage = self.fetch('/legal?page=legal')

        self.failIf(page.body != refPage.body,
                    "Withholding page argument did not redirect to legal page")

        # ensure help pages implement a jail for documents. redir to overview.
        page = self.fetch('/help?page=../frontPage')
        refPage = self.fetch('/help?page=overview')

        self.failIf(page.body != refPage.body,
                    "Illegal page reference was not contained.")

    def testBuild(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        self.addComponent("test:runtime", "1.0")
        self.addComponent("test:devel", "1.0")
        self.addCollection("test", "1.0", [ ":runtime", ":devel" ])

        self.addCollection('group-test', '1.0', ['test'])

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/testproject/newBuild')

        page = page.postForm(1, self.post, \
                             {'name' : 'Foo',
                              'distTroveName': 'group-test',
                              'distTroveVersion': '/testproject.' + \
                                  MINT_PROJECT_DOMAIN + '@rpl:devel/1.0-1-1',
                              'distTroveFlavor': '1#x86',
                              'buildtype_1' : '1'})

        cu = self.db.cursor()
        cu.execute("SELECT troveName FROM Builds")

        res = cu.fetchall()
        self.failIf(not res, "No build was generated from a web click.")
        self.failIf(res[0][0] != 'group-test',
                    "Trove name was malformed during build creation.")

    def testForPhantomBuildRows(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        cu = self.db.cursor()
        cu.execute("SELECT COUNT(buildId) FROM Builds")
        res = cu.fetchone()
        beforeCount = res[0]

        page = self.fetch('/project/testproject/newBuild')

        cu.execute("SELECT COUNT(buildId) FROM Builds")
        res = cu.fetchone()
        afterCount = res[0]

        self.failUnlessEqual(beforeCount, afterCount,
            "Hitting the build page creates a phantom row in builds table.")

    def testCantPublishBuildsWithoutFiles(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = self.newProject(client)

        build = client.newBuild(projectId, 'Test Build')
        build.setBuildType(1)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")

        self.webLogin('foouser', 'foopass')
        page = self.assertNotContent('/project/testproject/builds', 
            code = [200],
            content = 'href="publish?buildId',
            server = self.getProjectServerHostname())

    def testCreateExternalProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

    def testCreateMirroredProject(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'useMirror': '1',
                              'externalAuth': '1',
                              'externalUser': 'mirror',
                              'externalPass': 'mirrorpass',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getInboundLabels() == [[1, 1, 'https://conary.rpath.com/conary/', 'mirror', 'mirrorpass']])

        # and make sure that the 'shell' repository was created
        assert(os.path.exists(os.path.join(self.reposDir, 'repos', 'conary.rpath.com')))

    def testCreateExternalProjectNoAuth(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/external",
                                  'name="hostname" value="rpath"')

        page = page.postForm(1, self.post,
                             {'hostname' : 'rpath',
                              'name' : 'rPath Linux',
                              'label' : 'conary.rpath.com@rpl:devel',
                              'url' : '',
                              'operation' : 'process_external'})

        # ensure "first time" content does not appear on page
        page = self.assertNotContent("/admin/external",
                                     'name="hostname" value="rpath"')

        # and make sure that the appropriate database entries are created
        assert(client.getLabelsForProject(1) == ({'conary.rpath.com@rpl:devel': 1},
                                                 {'conary.rpath.com': 'http://conary.rpath.com/conary/'},
                                                 {'conary.rpath.com': ('anonymous', 'anonymous')}))

    def testCreateOutboundMirror(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        # ensure "first time" content appears on page
        page = self.assertContent("/admin/outbound",
            content = "No projects are currently mirrored")
        page = self.assertContent("/admin/addOutbound",
            content = "Project to mirror:")

        page = page.postForm(1, self.post,
            {'projectId':       str(projectId),
             'targetUrl':       'http://www.example.com/conary/',
             'mirrorUser':      'mirror',
             'mirrorPass':      'mirrorpass',
             'mirrorSources':   0})

        self.assertContent("/admin/outbound",
            content = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel")
        assert(client.getOutboundLabels() == \
            [[projectId, 1, 'http://www.example.com/conary/', 'mirror', 'mirrorpass', False, False]])
        assert(client.getOutboundMatchTroves(projectId) == \
               ['-.*:source', '-.*:debuginfo', '+.*'])

        page = self.fetch("/admin/outbound")
        page = page.postForm(1, self.post,
            {'remove':      '1 http://www.example.com/conary/',
             'operation':   'remove_outbound'})

        assert(client.getOutboundLabels() == [])
        assert(client.getOutboundMatchTroves(projectId) == [])

    def testCreateOutboundMirrorSources(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)

        self.webLogin('adminuser', 'adminpass')

        page = self.fetch("/admin/addOutbound")
        page = page.postForm(1, self.post,
            {'projectId':       str(projectId),
             'targetUrl':       'http://www.example.com/conary/',
             'mirrorUser':      'mirror',
             'mirrorPass':      'mirrorpass',
             'mirrorSources':   '1'})

        self.assertContent("/admin/outbound",
            content = "testproject." + MINT_PROJECT_DOMAIN + "@rpl:devel")
        assert(client.getOutboundLabels() == \
            [[projectId, 1, 'http://www.example.com/conary/', 'mirror', 'mirrorpass', False, False]])
        assert(client.getOutboundMatchTroves(projectId) == [])

    def testBrowseUsers(self):
        client, userId = self.quickMintAdmin('adminuser', 'adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/users", code = [200],
            content = '<a href="/userInfo?id=%d"' % userId)

    def testUserInfo(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        self.webLogin('testuser', 'testpass')

        page = self.assertContent("/userInfo?id=%d" % userId, code = [200],
            content = 'test at example.com')

    def testNotifyAllUsers(self):
        self.quickMintUser('localuser', 'localpass', email = 'test@localhost')
        self.quickMintUser('otheruser', 'otherpass', email = 'test@NONE')
        client, userId = self.quickMintAdmin('adminuser', 'adminpass',
                                             email = "test@NONE")

        self.webLogin('adminuser', 'adminpass')

        page = self.assertContent("/admin/notify",
            code = [200], content = 'value="notify_send"')

        page = page.postForm(1, self.post,
            {'subject':     'This is is my subject',
             'body':        'This is my body.',
             'operation':  'notify_send'})

        # make sure that our users were invalidated properly. admins and users
        # at localhost are expempted from invalidation
        self.assertRaises(database.ItemNotFound,
                          client.server._server.getConfirmation, 'adminuser')
        self.assertRaises(database.ItemNotFound,
                          client.server._server.getConfirmation, 'localuser')
        assert(client.server._server.getConfirmation('otheruser'))

    def testBrokenDownloadUrl(self):
        # for some reason lots of people do this and used to trigger a traceback:
        self.assertCode("/downloadImage/", code = 404)

    def testNoAdminPowers(self):
        self.assertCode("/admin/", code = 403)

    def testBrokenDNS(self):
        raise testsuite.SkipTestException
        client, userId = self.quickMintUser('testuser', 'testpass')
        self.webLogin('testuser', 'testpass')

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)
        self.assertContent("/project/testproject/", code = [200],
            content = "A DNS entry for this project's hostname", server = self.getProjectServerHostname())

        # a bit of a hack to create a project fqdn that will resolve
        projectId = client.newProject("Resolves", "test", "rpath.org")
        self.assertNotContent("/project/test/", code = [200],
            content = "A DNS entry for this project's hostname", server = self.getProjectServerHostname())

    def testForgotPassword(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        page = self.fetchWithRedirect('/forgotPassword')
        page = page.post("/resetPassword",
            {'username': 'testuser'})

        assert("An email with a new password has been sent" in page.body)

        # make sure the old password doesn't work
        self.assertRaises(AssertionError, 
            self.webLogin, 'testuser', 'testpass')

    def testBogusParameters(self):
        page = self.assertContent("/search?search=wobble&type=Packages&comment=imadirtyspammer",
            code = [200], content = "search() got an unexpected keyword argument 'comment'")


if __name__ == "__main__":
    testsuite.main()

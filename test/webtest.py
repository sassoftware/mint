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
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
import rephelp

from mint import mint_error
from mint import database
from mint import buildtypes
from mint import jobstatus
from mint import jsversion
from mint import urltypes

from repostest import testRecipe

from conary import versions
from conary.repository import errors

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def _checkRedirect(self, url, expectedRedirect, code=301):
        page = self.assertCode(url, code)
        redirectUrl = page.headers.getheader('location')
        self.failUnlessEqual(redirectUrl, expectedRedirect,
                "Expected redirect to %s, got %s" % \
                        (expectedRedirect, redirectUrl))

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
        pageURI = '/project/testproject/releases'
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

        self.clearCookies()

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

        # Test the registerComplete page
        page = self.fetchWithRedirect('/registerComplete')
        self.failIf('Thank you for registering' not in page.body,
                    'registerComplete failed')

        conf = client.server._server.getConfirmation('foouser')
        self.failIf(not conf, "Registration didn't add confirmation entry")

        page = self.assertCode("/confirm?id=%s" % conf, code = 200)

        self.failIf("Your account has now been confirmed." not in page.body,
                    "Confirmation Failed")
        page = self.assertCode("/confirm?id=%s" % conf, code = 200)
        self.failIf("Your account has already been confirmed." not in page.body,
                    "Multiple confirmations allowed.")

        page = self.fetchWithRedirect('/register')
        page = page.postForm(1, page.post,
                {'newUsername':  '',
                 'password':  '',
                 'password2': '',
                 'email':     '',
                 'email2':    '',
                 'tos':       '',
                 'privacy':   ''})
        self.failIf('You must supply a username.' not in page.body,
                    'Registration error not detected.')
        self.failIf('You must supply a valid e-mail address.' not in page.body,
                    'Registration error not detected.')
        self.failIf('Password field left blank.' not in page.body,
                    'Registration error not detected.')
        self.failIf('Password must be 6 characters or longer.' not in page.body,
                    'Registration error not detected.')
        self.failIf('You must accept the Terms of Service' not in page.body,
                    'Registration error not detected.')
        self.failIf('You must accept the Privacy Policy' not in page.body,
                    'Registration error not detected.')

        page = self.fetchWithRedirect('/register')
        page = page.postForm(1, page.post,
                {'newUsername':  'foo',
                 'password':  'pass1',
                 'password2': 'pass2',
                 'email':     'email1',
                 'email2':    'email2',
                 'tos':       'True',
                 'privacy':   'True'})
        self.failIf('Email fields do not match.' not in page.body,
                    'Registration error not detected.')
        self.failIf('Passwords do not match.' not in page.body,
                    'Registration error not detected.')

        page = self.fetchWithRedirect('/register')
        page = page.postForm(1, page.post,
                {'newUsername':  'foouser',
                 'password':  'passwd1',
                 'password2': 'passwd1',
                 'email':     'email1',
                 'email2':    'email1',
                 'tos':       'True',
                 'privacy':   'True'})
        self.failIf('An account with that username already exists.' not in page.body,
                    'Registration error not detected.')

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

    @testsuite.context("quick")
    def testBrowseProjects(self):
        self.registerErrorContent("Error")
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.editProject("", "Foo", "\xe2\x99\xaa utf-8 song and dance \xe2\x99\xaa")

        cu = self.db.cursor()
        r = cu.execute("INSERT INTO Commits VALUES(?, ?, 'whoCares', '1.0', ?)", projectId, 100, userId)
        self.db.commit()

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

    def testSearchUsers(self):
        client, userId = self.quickMintUser('foouser','foopass')
        adminClient, userId = self.quickMintAdmin('adminuser','adminpass')
        self.webLogin('adminuser', 'adminpass')

        page = self.fetch('/search?type=Users&search=foouser',
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


    def testEmptyBuildsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/builds/',
                                  content = 'contains no builds',
                                  code = [200])

    def testBuildsPage(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        self.webLogin('foouser', 'foopass')

        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/builds',
                content = "Kung Foo Fighting", code = [200])

        page = self.assertContent('/project/foo/build?id=%d' % build.id,
                content = "", code = [200])

        self.failUnless('300 MB' in page.body,
                "Missing build size information")
        self.failUnless(buildSha1 in page.body,
                "Missing build sha1 information")

        page = self.assertContent('/project/foo/editBuild?buildId=%d' % build.id,
                content = "Kung Foo Fighting", code = [200])

    def testBuildsPageMultipleFileUrls(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])
        fileId = build.getFiles()[0]['fileId']
        localUrlId = build.getFiles()[0]['fileUrls'][0][0]
        build.addFileUrl(fileId, urltypes.AMAZONS3,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso')
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso?torrent')

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/build?id=%d' % build.id,
                                  content = 'Kung Foo Fighting',
                                  code = [200])

        self.failUnless('urlType=%d' % urltypes.AMAZONS3TORRENT in page.body,
                "Missing S3 Torrent download link")
        self.failIf('urlType=%d' % urltypes.AMAZONS3 in page.body,
                "Amazon S3 link should override LOCAL type")
        self.failIf('urlType=%d' % urltypes.LOCAL in page.body,
                "LOCAL type shouldn't show up in URL")

        build.removeFileUrl(fileId, localUrlId)
        newpage = self.assertContent('/project/foo/build?id=%d' % build.id,
                                  content = 'Kung Foo Fighting',
                                  code = [200])

        self.failIf('urlType=%d' % urltypes.AMAZONS3 in newpage.body,
                "Removing LOCAL type with S3 in place should not change the page")

    def testEmptyReleasesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/releases/',
                                  content = 'has no releases',
                                  code = [200])

    def testReleasesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        release = client.newPublishedRelease(projectId)
        release.name = "Foo Fighters"
        release.version = "0.1"
        release.addBuild(build.id)
        release.save()

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/releases/',
                                  content = 'Foo Fighters',
                                  code = [200])

        page = self.assertContent('/project/foo/release?id=%d' % release.id,
                content = 'Foo Fighters', code = [200])

        self.failUnless('300 MB' in page.body,
                "Missing build size information")
        self.failUnless(buildSha1 in page.body,
                "Missing build sha1 information")

    def testReleasesPageMultipleFileUrls(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])
        fileId = build.getFiles()[0]['fileId']
        localUrlId = build.getFiles()[0]['fileUrls'][0][0]
        build.addFileUrl(fileId, urltypes.AMAZONS3,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso')
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso?torrent')

        release = client.newPublishedRelease(projectId)
        release.name = "Foo Fighters"
        release.version = "0.1"
        release.addBuild(build.id)
        release.save()

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/release?id=%d' % release.id,
                                  content = 'Foo Fighters',
                                  code = [200])

        self.failUnless('urlType=%d' % urltypes.AMAZONS3TORRENT in page.body,
                "Missing S3 Torrent download link")
        self.failIf('urlType=%d' % urltypes.AMAZONS3 in page.body,
                "Amazon S3 link should override LOCAL type")
        self.failIf('urlType=%d' % urltypes.LOCAL in page.body,
                "LOCAL type shouldn't show up in URL")

        build.removeFileUrl(fileId, localUrlId)
        newpage = self.assertContent('/project/foo/release?id=%d' % release.id,
                                  content = 'Foo Fighters',
                                  code = [200])

        self.failIf('urlType=%d' % urltypes.AMAZONS3 in newpage.body,
                "Removing LOCAL type with S3 in place should not change the page")

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
        page = self.webLogin('foouser', 'foopass')
        page = self.assertContent('/uploadKey', code = [200],
                               content = "you are not a member of any projects")
        page = page.fetchWithRedirect('/logout')

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
        raise testsuite.SkipTestException("webunit bug: mixing of hidden and checkbox fields on the page")
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

        project = client.getProject(projectId)

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
        build.setFiles([['test.iso', 'Test Image']])

        expectedLocalRedirect = 'http://%s.%s:%d/images/foo/%d/test.iso' % \
                (MINT_HOST, MINT_DOMAIN, self.port, build.id)

        # the following should all be equivalent
        self._checkRedirect('/downloadImage/1', expectedLocalRedirect)
        self._checkRedirect('/downloadImage/1/test.iso', expectedLocalRedirect)
        self._checkRedirect('/downloadImage?fileId=1', expectedLocalRedirect)
        self._checkRedirect('/downloadImage/test.iso?fileId=1', expectedLocalRedirect)

        # this should return 404
        page = self.assertCode('/downloadImage/1/not_really.iso', code = 404)

        # so should this
        page = self.assertCode('/downloadImage/1337', code = 404)

    def testDownloadISOWithUrlType(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)
        build.setFiles([['test.iso', 'Test Image']])
        files = build.getFiles()
        assert(len(files) == 1)
        fileId = files[0]['fileId']
        expectedLocalRedirect = 'http://%s.%s:%d/images/foo/%d/test.iso' % \
                (MINT_HOST, MINT_DOMAIN, self.port, build.id)
        expectedRemoteRedirect = 'http://foo.elsewhere.org/'
        build.addFileUrl(fileId, urltypes.GENERICMIRROR, expectedRemoteRedirect)

        # sanity checks
        self._checkRedirect('/downloadImage/1', expectedLocalRedirect)

        self._checkRedirect('/downloadImage/1?urlType=%d' % urltypes.LOCAL,
                expectedLocalRedirect)

        self._checkRedirect('/downloadImage/1?urlType=%d' % urltypes.GENERICMIRROR,
                expectedRemoteRedirect)

        self._checkRedirect('/downloadImage/1/test.iso?urlType=%d' % urltypes.LOCAL,
                expectedLocalRedirect)
        
        self._checkRedirect('/downloadImage/1/test.iso?urlType=%d' % urltypes.GENERICMIRROR,
                expectedRemoteRedirect)

        self._checkRedirect('/downloadImage/1/test.iso?fileId=1&urlType=%d' % urltypes.LOCAL,
                expectedLocalRedirect)
        
        self._checkRedirect('/downloadImage/1/test.iso?fileId=1&urlType=%d' % urltypes.GENERICMIRROR,
                expectedRemoteRedirect)

        # these should return 404
        page = self.assertCode('/downloadImage/1?urlType=%d' % \
                urltypes.AMAZONS3, code = 404)

        page = self.assertCode('/downloadImage/1/test.iso?urlType=%d' % \
                urltypes.AMAZONS3, code = 404)

        page = self.assertCode('/downloadImage/test.iso?fileId=1&urlType=%d' % \
                urltypes.AMAZONS3, code = 404)

        # and so should these
        page = self.assertCode('/downloadImage/1?urlType=1337', code = 404)

        page = self.assertCode('/downloadImage/1/test.iso?urlType=1337',
                code = 404)

        page = self.assertCode('/downloadImage/test.iso?fileId=1&urlType=1337',
                code = 404)

    def testDownloadISOWithAmazonOverride(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        projectId = client.newProject("Foo", "foo", MINT_PROJECT_DOMAIN)
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)
        build.setFiles([['test.iso', 'Test Image']])
        files = build.getFiles()
        assert(len(files) == 1)
        localUrlId = build.getFiles()[0]['fileUrls'][0][0]
        fileId = files[0]['fileId']
        expectedRemoteRedirect = 'http://s3.amazonaws.com/ExtraCrispyChicken/test.iso'
        build.addFileUrl(fileId, urltypes.AMAZONS3, expectedRemoteRedirect)

        # these all should forward to amazon
        self._checkRedirect('/downloadImage/1', expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso', expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/test.iso?fileId=1',
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/?urlType=%d' % urltypes.AMAZONS3,
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/?urlType=%d' % urltypes.LOCAL,
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso?urlType=%d' %\
                urltypes.LOCAL, expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso?fileId=1&urlType=%d' %\
                urltypes.LOCAL, expectedRemoteRedirect)

        build.removeFileUrl(fileId, localUrlId)

        # these should still work
        self._checkRedirect('/downloadImage/1', expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso', expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/test.iso?fileId=1',
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/?urlType=%d' % urltypes.AMAZONS3,
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/?urlType=%d' % urltypes.LOCAL,
                expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso?urlType=%d' %\
                urltypes.LOCAL, expectedRemoteRedirect)
        self._checkRedirect('/downloadImage/1/test.iso?fileId=1&urlType=%d' %\
                urltypes.LOCAL, expectedRemoteRedirect)

        cu = self.db.cursor()
        cu.execute("SELECT * FROM UrlDownloads")
        x = cu.fetchall()
        self.failUnlessEqual(14, len(x))

    def testUtf8ProjectName(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)

        project.editProject("http://example.com/",
            'My linux is free, cool\xe7',
            "Test Title")
        project.refresh()

        page = self.assertContent('/project/foo/', code = [200],
            content = project.getDesc().decode("latin1").encode("utf-8"),
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

        troveSpec = 'group-test=/testproject.' + MINT_PROJECT_DOMAIN + '@rpl:devel/0.0:1.0-1-1' + '[is: x86]'
        page = page.postForm(1, self.post,
                             {'name' : 'Foo',
                              'distTroveSpec': troveSpec,
                              'anaconda_templatesSpec': troveSpec,
                              'buildtype_1' : '1'})

        cu = self.db.cursor()
        cu.execute("SELECT buildId, troveName FROM Builds")

        res = cu.fetchall()
        self.failIf(not res, "No build was generated from a web click.")
        buildId = res[0][0]
        self.failIf(res[0][1] != 'group-test',
                    "Trove name was malformed during build creation.")

        build = client.getBuild(buildId)
        assert(build.getDataValue('anaconda-templates') == 
            'group-test=/testproject.%s@rpl:devel/1.0-1-1[is: x86]' % MINT_PROJECT_DOMAIN)

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

    def testUserInfo(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        client2, userId2 = self.quickMintUser('foouser', 'foopass')
        self.webLogin('testuser', 'testpass')

        page = self.assertContent("/userInfo?id=%d" % userId, code = [200],
            content = 'test at example.com')

        projectId1 = client2.newProject("Foo", "testproject",
                                        MINT_PROJECT_DOMAIN)
        projectId2 = client2.newProject("Bar", "Barproject", 
                                        MINT_PROJECT_DOMAIN)
        adminClient, userId = self.quickMintAdmin('adminuser','adminpass')
        adminClient.hideProject(projectId1)
        page = self.fetch('/userInfo?id=%d' % userId2)
        self.failUnless('Barproject' in page.body,
                        'Visible project was hidden.')
        self.failIf('testproject' in page.body,
                        'Hidden project was visible.')
        self.assertContent('/userInfo?id=1000', 'Please go back and try again')

    def testBrokenDownloadUrl(self):
        # for some reason lots of people do this and used to trigger a traceback:
        self.assertCode("/downloadImage/", code = 404)

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

    def testUtf8Rss(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        self.webLogin('testuser', 'testpass')

        projectId = client.newProject("Foo", "testproject", MINT_PROJECT_DOMAIN)
        project = client.getProject(projectId)
        project.editProject("", "Foo", "\xe2\x99\xaa utf-8 song and dance \xe2\x99\xaa")

        cu = self.db.cursor()
        r = cu.execute("INSERT INTO Commits VALUES(?, ?, 'whoCares', '1.0', ?)", projectId, 100, userId)
        self.db.commit()

        self.assertCode("/rss?feed=newProjects", code = 200)

        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Bar', 'foo', MINT_PROJECT_DOMAIN)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])
        fileId = build.getFiles()[0]['fileId']
        localUrlId = build.getFiles()[0]['fileUrls'][0][0]
        build.addFileUrl(fileId, urltypes.AMAZONS3,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso')
        build.addFileUrl(fileId, urltypes.AMAZONS3TORRENT,
                'http://s3.amazonaws.com/ExtraCrispyChicken/foo.iso?torrent')

        release = client.newPublishedRelease(projectId)
        release.name = "Foo Fighters"
        release.version = "0.1"
        release.addBuild(build.id)
        release.save()
        release.publish()
        
        self.assertContent('/rss?feed=newReleases', 
                           content='Kung Foo Fighting (x86 Stub)&lt',
                           code=[200])
        self.assertCode('/rss?feed=fakeFeed', code=404)


if __name__ == "__main__":
    testsuite.main()

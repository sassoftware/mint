#!/usr/bin/python
#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import cPickle
import os
import urlparse

from mint_test import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN, FQDN
import rephelp

from mint import mint_error
from mint.lib import database
from mint.lib import data
from mint import buildtypes
from mint import jobstatus
from mint import urltypes
from mint import helperfuncs

from repostest import testRecipe
from testrunner import pathManager

from conary.lib import util
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

        self.failUnless(FQDN in self.cookies.keys(),
                "%s missing from cookies" % FQDN)

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
        hostname = "foo"
        self.newProject(client, 'Foo', hostname)

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
        self.db.commit()

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

        if self.mintCfg.sendNotificationEmails:
            conf = client.server._server.getConfirmation('foouser')
            self.failIf(not conf, "Registration didn't add confirmation entry")

            page = self.assertCode("/confirm?id=%s" % conf, code = 200)

            self.failIf("your account has now been confirmed" not in page.body.lower(),
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
        if self.mintCfg.rBuilderOnline or self.mintCfg.tosLink:
            self.failIf('You must accept the Terms of Service' not in page.body,
                        'Registration error not detected.')
        if self.mintCfg.rBuilderOnline or self.mintCfg.privacyPolicyLink:
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

    def testNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        page = page.postForm(1, self.fetchWithRedirect,
                {'title': 'Test Project', 'shortname': 'test',
                    'domainname': MINT_PROJECT_DOMAIN,
                    'prodtype': 'Component',
                    'version': '1.0',
                    'platformLabel': '',
                    })

        project = client.getProjectByHostname("test")
        self.failUnlessEqual(project.getName(), 'Test Project')
        self.failUnlessEqual(project.getApplianceValue(), 'no')
        self.failUnlessEqual(project.getLabel(),
            "test." + MINT_PROJECT_DOMAIN +
            '@rpl:2')


    def testApplianceFlagYesNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        page = page.postForm(1, self.fetchWithRedirect,
                {'title': 'Test Project', 'hostname': 'test',
                 'domainname': MINT_PROJECT_DOMAIN,
                 'shortname': 'test',
                 'isPrivate': False,
                 'prodtype': 'Appliance',
                 'namespace': self.mintCfg.namespace,
                 'version': '1.0',
                 'platformLabel': '',
                 })

        project = client.getProjectByHostname("test")
        self.failUnlessEqual(project.getApplianceValue(), 'yes')

    def testApplianceFlagNoNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        page = page.postForm(1, self.fetchWithRedirect,
                {'title': 'Test Project 2', 'shortname': 'test2',
                 'domainname': MINT_PROJECT_DOMAIN,
                 'prodtype': 'Component',
                 'version': '1.0',
                 'platformLabel': '',
                 })

        project = client.getProjectByHostname("test2")
        self.failUnlessEqual(project.getApplianceValue(), 'no')

    def testApplianceFlagUnknownNewProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        page = page.assertCode('/newProject', code = 200)

        page = page.postForm(1, self.fetchWithRedirect,
                {'title': 'Test Project 3', 'shortname': 'test3',
                 'domainname': MINT_PROJECT_DOMAIN,
                 'prodtype': 'Component',
                 'version': '1.0',
                 'platformLabel': '',
                 })

        project = client.getProjectByHostname("test3")
        self.failUnlessEqual(project.getApplianceValue(), 'no')

    def testEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertCode('/project/foo/editProject', code = 200)

    def testProcessEditProject(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'Bar',
                           'commitEmail': 'email@example.com',
                           'namespace': 'spacemonkey'},
                          ok_codes = [302])

        project = client.getProject(projectId)
        self.failUnlessEqual(project.name, 'Bar')
        self.failUnlessEqual(project.commitEmail, 'email@example.com')
        self.failUnlessEqual(project.namespace, 'spacemonkey')
        
    def testProcessEditProjectVisibilityPublicToPrivate(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'Bar',
                           'isPrivate': 'on'},
                          ok_codes = [200])

        project = client.getProject(projectId)
        # not allowed, so should still be public
        self.failUnlessEqual(project.hidden, False)
        
    def testProcessEditProjectVisibilityPrivateToPublic(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component",
                        isPrivate = True)
        page = self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/processEditProject', postdata =
                          {'name'   : 'Bar',
                           'isPrivate': 'off',
                           'namespace': 'spacemonkey'},
                          ok_codes = [302])

        project = client.getProject(projectId)
        self.failUnlessEqual(project.hidden, False)

    @testsuite.context("quick")
    def testSearchProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        project = client.getProject(projectId)
        project.editProject("", "Foo", "\xe2\x99\xaa utf-8 song and dance \xe2\x99\xaa")

        page = self.fetch('/search?type=Projects&search=foo',
                          ok_codes = [200])

        assert('Search Results:') in page.body

    def testSearchPackages(self):
        page = self.fetch('/search?type=Packages&search=%25%25%25',
                          ok_codes = [200])

        assert('Search Results:') in page.body
        page = self.fetch('/search?type=Packages&search=foo%3Dconary.rpath.com%40rpl%3A1',
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
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/', 
                ok_codes = [200])

    def testMembersPage(self):
        self.quickMintUser('testuser','testpass')
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.fetch('/project/foo/members/', 
                ok_codes = [200])
        page = page.postForm(1, self.post, {'username' : 'testuser',
                                            'level' : 0})


    def testEmptyImagesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                            shortname=hostname, version="1.0", prodtype="Component")

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/builds/',
                                  content = 'contains no images',
                                  code = [200])

    def testBuildsPage(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])
        self.setBuildFinished(build.buildId)

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
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

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
        self.setBuildFinished(build.buildId)

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

    @testsuite.tests('RBL-2600', 'RBL-3251', 'RBL-3259')
    def testBuildPageAnacondaCustomFields(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])
        build.setDataValue('anaconda-custom',
                'anaconda-custom=/conary.rpath.com@rpl:devel/2.0-1-1[]',
                data.RDT_TROVE, validate=False)
        self.setBuildFinished(build.buildId)

        # make one of these frozen just to make sure we can handle
        # cases where a frozen version made it into the database
        build.setDataValue('anaconda-templates',
                'anaconda-templates=/conary.rpath.com@rpl:devel/1216663633.443:2.0-2-1[is: x86]', data.RDT_TROVE, validate=False)

        build.setDataValue('media-template',
                'media-template=/conary.rpath.com@rpl:devel//foresight.rpath.org@fl:1/3.0-1.1-1[]', data.RDT_TROVE, validate=False)

        self.webLogin('foouser', 'foopass')

        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/builds',
                content = "Kung Foo Fighting", code = [200])

        page = self.fetch('/project/foo/build?id=%d' % build.id)

        self.failUnless('conary.rpath.com@rpl:devel/2.0-1-1' \
                in page.body)
        self.failUnless('conary.rpath.com@rpl:devel/2.0-2-1' \
                in page.body)
        self.failUnless('foresight.rpath.org@fl:1/3.0-1.1-1' \
                in page.body)

        # Now set one of the fields as NONE and make sure it doesn't show up
        build.setDataValue('anaconda-custom',
                'NONE', data.RDT_TROVE, validate=False)

        page = self.assertNotContent('/project/foo/build?id=%d' % build.id,
                content = 'Custom')
        page = self.assertNotContent('/project/foo/build?id=%d' % build.id,
                content = 'NONE')


    def testEmptyReleasesPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/releases/',
                                  content = 'has no releases',
                                  code = [200])

        page = self.assertCode('/project/foo/latestRelease', code = 302)

    def testReleasesPage(self):
        from mint import userlevels
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        project = client.getProject(projectId)
        devClient, userId = self.quickMintUser('devuser','devpass')
        project.addMemberByName('devuser', userlevels.DEVELOPER)

        build = client.newBuild(projectId, 'Kung Foo Fighting')
        build.setDesc("It's a little bit frightening!")
        build.setBuildType(buildtypes.STUB_IMAGE)
        build.setTrove("group-trove",
            "/conary.rpath.com@rpl:devel/0.0:1.0-1-1", "1#x86")
        buildSize = 1024 * 1024 * 300
        buildSha1 = '0123456789ABCDEF01234567890ABCDEF0123456'
        build.setFiles([['foo.iso', 'Foo ISO Image', buildSize, buildSha1]])

        release = devClient.newPublishedRelease(projectId)
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

        # make sure /latestRelease redirects to latest release
        self.assertCode('/project/foo/latestRelease', code = 302)
        try:
            devClient.publishPublishedRelease(release.id, False)
            assert(0)
        except mint_error.PermissionDenied, e:
            # make sure we get permission denied when trying to
            # publish as a developer
            pass
        client.publishPublishedRelease(release.id, False)


    def testReleasesPageMultipleFileUrls(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

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

    def testOldReleasePage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

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

        cu = self.db.cursor()
        cu.execute('''UPDATE PublishedReleases SET timeCreated = NULL,
            timeUpdated = NULL WHERE pubReleaseId = ?''', release.id)
        self.db.commit()

        self.webLogin('foouser', 'foopass')

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        page = self.assertContent('/project/foo/releases/',
                                  content = 'Foo Fighters',
                                  code = [200])

        page = self.assertContent('/project/foo/release?id=%d' % release.id,
                content = 'Foo Fighters', code = [200])

        self.failIf('Release created' in page.body,
            'Created time should not be in response')
        self.failIf('Release updated' in page.body,
            'Updated time should not be in response')

    def testMailListsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

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

    def testUploadKeyPage(self):
        pText = helperfuncs.getProjectText().lower()
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        page = self.assertContent('/uploadKey', code = [200],
                               content = "you are not a member of any %ss"%pText)
        page = page.fetchWithRedirect('/logout')

        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        page = self.assertContent('/uploadKey', code = [200],
                                 content = "Permission Denied")

        page = self.webLogin('foouser', 'foopass')

        page = self.assertNotContent('/uploadKey', code = [200],
                                 content = "Permission Denied")


    def testUploadKey(self):
        keyFile = open(pathManager.getPath('MINT_ARCHIVE_PATH') + '/key.asc')
        keyData = keyFile.read()
        keyFile.close()
        client, userId = self.quickMintUser('foouser','foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/processKey', postdata =
                          {'projects' : ['foo'],
                           'keydata' : keyData})
        if 'error' in page.body:
            self.fail('Posting OpenPGP Key to project failed.')

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
        hostname = 'foo'
        projectId = self.newProject(client, 'Foo', hostname)

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

        page = page.fetchWithRedirect('/',
                server = self.getProjectServerHostname())
        self.failIf("Email Confirmation Required" not in page.body,
                    'Unconfirmed user broke out of confirm email jail on'
                    ' front page.')

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
        self.failIf("your account has now been confirmed" not in
                page.body.lower(), 'Unconfirmed user was unable to confirm.')

    def testSessionStability(self):
        newSid = '1234567890ABCDEF1234567890ABCDEF'.lower()
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
        page = self.fetch('/', ok_codes = [200])

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
            content = 'An unknown error occurred',
            server = self.getProjectServerHostname())

    def testDownloadISO(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        hostname = 'foo'
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)
        build.setFiles([[self.mintCfg.imagesPath + '/test.iso', 'Test Image']])

        util.mkdirChain(self.mintCfg.imagesPath)
        f = open(self.mintCfg.imagesPath + '/test.iso', 'w')
        f.close()

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

    def testDownloadHugeImage(self):
        if not os.path.exists("/usr/bin/curl"):
            raise testsuite.SkipTestException("please install curl")
        client, userId = self.quickMintUser("testuser", "testpass")
        hostname = 'foo'
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)
        build.setFiles([[self.mintCfg.imagesPath + '/huge.iso', 'Test Image']])

        util.mkdirChain(self.mintCfg.imagesPath)
        huge = self.mintCfg.imagesPath + '/huge.iso'
        f = open(huge, 'w')
        f.seek(long(4.5 * 1024 * 1024 * 1024))
        f.write('1')
        f.close()

        url = "http://%s:%d/downloadImage/1" % self.getServerData()
        f = os.popen("curl -s %s | md5sum" % url)

        self.failUnless('91f30ef9e0212d71519da306782972b0' in f.read())

    def testDownloadISOWithUrlType(self):
        client, userId = self.quickMintUser("testuser", "testpass")
        hostname = 'foo'
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        build = client.newBuild(projectId, "Test Build")
        build.setBuildType(0)
        build.setFiles([[self.mintCfg.imagesPath + '/test.iso', 'Test Image']])
        files = build.getFiles()
        assert(len(files) == 1)
        fileId = files[0]['fileId']
        expectedLocalRedirect = 'http://%s.%s:%d/images/foo/%d/test.iso' % \
                (MINT_HOST, MINT_DOMAIN, self.port, build.id)
        expectedRemoteRedirect = 'http://foo.elsewhere.org/'
        build.addFileUrl(fileId, urltypes.GENERICMIRROR, expectedRemoteRedirect)

        util.mkdirChain(self.mintCfg.imagesPath)
        f = open(self.mintCfg.imagesPath + '/test.iso', 'w')
        f.close()

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
        hostname = 'foo'
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
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
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        project = client.getProject(projectId)

        project.editProject("http://example.com/",
            'My linux is free, cool\xe7',
            "Test Title")
        project.refresh()

        page = self.assertContent('/project/foo/', code = [200],
            content = project.getDesc().decode("latin1").encode("utf-8"),
            server = self.getProjectServerHostname())

    def testProjectReg(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = self.newProject(client)

        # we are working with the project server right now
        self.setServer(self.getProjectServerHostname(), self.port)

        # link historically showed up wrong by not pre-pending a /
        page = self.assertNotContent('/project/testproject/',
                                     'a href="register"')

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

    def testBuild(self):
        raise testsuite.SkipTestException("MCP not stubbed in web code")
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
        page = page.postForm(2, self.post,
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

        hostname = 'testproject'
        projectId1 = client2.newProject("Foo", hostname,
                                        MINT_PROJECT_DOMAIN,
                                        shortname=hostname,
                                        version="1.0", prodtype="Component")
        hostname="Barproject"
        projectId2 = client2.newProject("Bar", hostname,
                                        MINT_PROJECT_DOMAIN,
                                        shortname=hostname,
                                        version="1.0", prodtype="Component")
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
        '''Unknown parameters should be silently ignored.'''
        page = self.assertContent("/search?search=wobble&type=Packages&comment=imadirtyspammer",
            code = [200], content = "Search Results")

    def testUtf8Rss(self):
        client, userId = self.quickMintUser('testuser', 'testpass')
        self.webLogin('testuser', 'testpass')

        hostname="testproject"
        projectId = client.newProject("Foo", hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        project = client.getProject(projectId)
        project.editProject("", "Foo", "\xe2\x99\xaa utf-8 song and dance \xe2\x99\xaa")

        cu = self.db.cursor()
        r = cu.execute("INSERT INTO Commits VALUES(?, ?, 'whoCares:source', '/restproject.rpath.local@foo:1/1.0.1-1', ?)", projectId, 100, userId)
        self.db.commit()

        self.assertCode("/rss?feed=newProjects", code = 200)

        client, userId = self.quickMintUser('foouser','foopass')
        hostname="foo"
        projectId = client.newProject('Bar', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")

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

        self.setServer(self.getProjectServerHostname(), self.port)

        self.assertContent('/project/foo/rss',
                content='Kung Foo Fighting (x86 Stub)&lt', code=[200])

        self.assertContent('/project/testproject/rss?feed=commits',
                content='whoCares:source', code=[200])

    def testPwCheck(self):
        client, userid = self.quickMintUser('testuser', 'testpass')
        from conary.repository.netrepos.netauth import PasswordCheckParser

        if self.mintCfg.SSL:
            serverName = self.getServerData()[0]
            url = 'https://%s:%s' % (serverName, self.securePort)
            # ensure that accessing via non-HTTPS says valid=false
            x = PasswordCheckParser()
            x.parse(self.fetch('/pwCheck?user=testuser;password=testpass').body)
            assert not x.validPassword()
        else:
            url = ''

        x = PasswordCheckParser()
        x.parse(self.fetch('%s/pwCheck?user=testuser;password=testpass' %url).body)
        assert x.validPassword()

        x = PasswordCheckParser()
        x.parse(self.fetch('%s/pwCheck?user=baduser;password=testpass' %url).body)
        assert not x.validPassword()

        x = PasswordCheckParser()
        x.parse(self.fetch('%s/pwCheck?user=testuser;password=badpw' %url).body)
        assert not x.validPassword()

        x = PasswordCheckParser()
        x.parse(self.fetch('%s/pwCheck?user=' %url).body)
        assert not x.validPassword()

    def testBulletin(self):
        bulletinContent = """rBuilder Online will be down for maintenance"""
        XMLbulletinContent = """<DIV>rBuilder Online will be down for maintenance, see <A HREF="http://blogs.conary.com/">Conary Blogs</A> for announcements</DIV>"""

        # gotta be logged in, otherwise frontPage caching will kill us
        self.quickMintUser('foouser','foopass')
        self.webLogin('foouser', 'foopass')

        # Sanity check
        self.assertCode('/', code=[200])

        # Make sure bulletin text not there
        page = self.fetch('/')
        self.failIf(bulletinContent in page.body)

        # Put bulletin text in a file
        bf = open(self.mintCfg.bulletinPath, 'w')
        bf.write(bulletinContent)
        bf.close()

        # Make sure it shows up on the home page
        page = self.fetch('/')
        self.assertContent('/', content=bulletinContent)

        # Remove file; make sure it goes away
        os.unlink(self.mintCfg.bulletinPath)
        page = self.fetch('/')
        self.failIf(bulletinContent in page.body)

        # Put XML bulletin text in a file and make sure it works
        bf = open(self.mintCfg.bulletinPath, 'w')
        bf.write(XMLbulletinContent)
        bf.close()
        self.assertContent('/', content=XMLbulletinContent)

    def testFrontPageBlock(self):
        HTMLcontent = """<DIV>The MARKETING block of code</DIV>"""

        # gotta be logged in, otherwise frontPage caching will kill us
        self.quickMintUser('foouser','foopass')
        self.webLogin('foouser', 'foopass')

        # Sanity check
        self.assertCode('/', code=[200])

        # Make sure marketing block is not there
        page = self.fetch('/')
        self.failIf(HTMLcontent in page.body)

        # Put content into file
        f = open(self.mintCfg.frontPageBlock, 'w')
        f.write(HTMLcontent)
        f.close()

        # Check it is on page
        page = self.fetch('/')
        self.assertContent('/', content=HTMLcontent)

    def addExternalRepository(self, client, userpass=('test', 'foo'),
                              serverIdx=0):
        # make sure mint has started
        # and that we're using that mint repos as a proxy.
        repos = self.startMintServer(useProxy=True)
        repos = self.openConaryRepository(serverIdx)
        hostname = 'localhost'
        if serverIdx:
            hostname += str(serverIdx)
        repos.deleteUserByName('%s@rpl:1' % hostname, 'anonymous')
        if not userpass:
            userpass = ('', '')
        extLabel = hostname + '@rpl:linux'
        projectId = client.newExternalProject(hostname, hostname, '',
                                            extLabel,
                                            self.cfg.repositoryMap[hostname],
                                            mirror=False)

        project = client.getProject(projectId)
        labelIdMap = client.getLabelsForProject(projectId)[0]
        label, labelId = labelIdMap.items()[0]
        authType = 'userpass'
        project.editLabel(labelId, extLabel, self.cfg.repositoryMap[hostname],
                          authType, userpass[0], userpass[1], '')
        return repos, hostname

    def editExternalRepository(self, client, hostname, 
                              userpass=('test', 'foo')):
        project = client.getProjectByHostname(hostname)
        labelIdMap = client.getLabelsForProject(project.projectId)[0]
        label, labelId = labelIdMap.items()[0]
        extLabel = hostname + '@rpl:linux'
        authType = 'userpass'
        project.editLabel(labelId, extLabel, self.cfg.repositoryMap[hostname],
                          authType, userpass[0], userpass[1], '')

    def testGetAvailablePlatforms(self):
        client = self.startMintServer(useProxy=True)
        platforms = client.getAvailablePlatforms()
        self.assertEquals(platforms, [['localhost@rpl:plat',
                'My Spiffy Platform']])

    def testGetAllImagesByType(self):
        client, userId = self.quickMintUser('foouser', 'foopass')
        adminClient, userId2 = self.quickMintAdmin('foo2', 'foo2')
        otherClient, userId3 = self.quickMintUser('foo3', 'foo3')
        projectId = self.newProject(client)
        projectId2 = self.newProject(otherClient, 'testproject2', 'tp2')

        # check permissions - users can see their own, admin can see all.
        self.addBuild(client, projectId, buildtypes.XEN_OVA, userId=userId)
        self.addBuild(client, projectId2, buildtypes.XEN_OVA, userId=userId3)
        images = client.getAllBuildsByType('XEN_OVA')
        assert(len(images) == 1)
        self.failUnless('buildPageUrl' in images[0], images[0])

        images = otherClient.getAllBuildsByType('XEN_OVA')
        assert(len(images) == 1)
        images = adminClient.getAllBuildsByType('XEN_OVA')
        assert(len(images) == 2)

        images = client.getAllBuildsByType('VMWARE_ESX_IMAGE')
        assert(len(images) == 0)
        self.addBuild(client, projectId, buildtypes.VMWARE_ESX_IMAGE,
                      userId=userId)
        images = client.getAllBuildsByType('VMWARE_ESX_IMAGE')
        assert(len(images) == 1)
        self.failUnlessEqual(len(images[0]['files']), 1)

        images = client.getAllBuildsByType('VMWARE_OVF_IMAGE')
        assert(len(images) == 0)
        self.addBuild(client, projectId, buildtypes.VMWARE_OVF_IMAGE,
                      userId=userId)
        images = client.getAllBuildsByType('VMWARE_OVF_IMAGE')
        assert(len(images) == 1)

        images = client.getAllBuildsByType('AMI')
        assert(len(images) == 0)
        self.addBuild(client, projectId, buildtypes.AMI,
                      userId=userId)
        self.addBuild(client, projectId, buildtypes.AMI,
                      userId=userId, buildData={'amiId' : '324'})
        images = client.getAllBuildsByType('AMI')
        assert(len(images) == 1)

        # Check VWS - 
        images = client.getAllBuildsByType('VWS')
        assert(len(images) == 0)
        self.addBuild(client, projectId, buildtypes.RAW_FS_IMAGE,
                      userId=userId)
        images = client.getAllBuildsByType('VWS')
        assert(len(images) == 0)
        self.addBuild(client, projectId, buildtypes.RAW_FS_IMAGE,
                      userId=userId, buildData={'XEN_DOMU' : True})
        images = client.getAllBuildsByType('VWS')
        self.failUnlessEqual(len(images), 1)
        image = images[0]
        expected = {
            'productDescription': '', 'buildId': 8, 'projectId': 1,
            'isPublished': 0, 'buildDescription': 'Build Description',
            'productName': 'Test Project',
            'isPrivate': 0,
            'sha1': 'fe5dbbcea5ce7e2988b8c69bcfdfde8904aabc1f',
            'role': 'Product Owner', 'createdBy': 'foouser',
            'buildName': 'Build', 'baseFileName': 'testproject-0.1-',
            'downloadUrl': 'http://SOMEHOST/downloadImage?fileId=8',
            'buildPageUrl': 'http://SOMEHOST/project/testproject/build?id=8',
            'files' : [
                {'downloadUrl': 'http://SOMEHOST/downloadImage?fileId=8',
                 'sha1': 'fe5dbbcea5ce7e2988b8c69bcfdfde8904aabc1f',
                 'idx': 0,
                 'size': '8192',
                 'filename' : 'imageFile 8',
                 },
            ],
        }
        image['downloadUrl'] = self._whiteOutHostPort(image['downloadUrl'])
        image['buildPageUrl'] = self._whiteOutHostPort(image['buildPageUrl'])
        for f in image['files']:
            f['downloadUrl'] = self._whiteOutHostPort(f['downloadUrl'])
        self.failUnlessEqual(images[0], expected)

    @classmethod
    def _whiteOutHostPort(cls, url):
        arr = url.split('/')
        arr[2] = 'SOMEHOST'
        return '/'.join(arr)

if __name__ == "__main__":
    testsuite.main()

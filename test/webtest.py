#!/usr/bin/python2.4
#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
import testsuite
testsuite.setup()

import mint_rephelp

class MintTest(mint_rephelp.WebRepositoryHelper):
    def testNoLocalRedirect(self):
        page = self.assertCode('', code = 200)
        if self.cookies == {}:
            self.fail("Web Server did not set session cookie")

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

# FIXME: implement skipped tests.
# FIXME: these tests can't be run until mint shims pages in the /repos stack.
#    def testPgpAdminPage(self):
#        raise SkipTestException
#        client, userId = self.quickMintUser('foouser','foopass')
#        projectId = client.newProject('Foo', 'foo', 'rpath.local')
#
#        page = self.fetch('/repos/foo/pgpAdminForm',
#                                  ok_codes = [200])

#    def testRepoBrowserPage(self):
#        client, userId = self.quickMintUser('foouser','foopass')
#        projectId = client.newProject('Foo', 'foo', 'rpath.local')
#
#        page = self.assertContent('/repos/foo/browse',
#                                  ok_codes = [200],
#                                  content = 'Repository Browser')

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

if __name__ == "__main__":
    testsuite.main()

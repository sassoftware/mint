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

    def testSearchProjects(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('/search?type=Projects&search=foo',
                          ok_codes = {200: ''})
        assert('match found for') in page.body

    def testProjectsPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('')
        page = page.fetch('/project/foo/', ok_codes = {200: ''})

    def testMembersPage(self):
        client, userId = self.quickMintUser('foouser','foopass')
        projectId = client.newProject('Foo', 'foo', 'rpath.local')

        page = self.fetch('')
        page = page.fetch('/project/foo/members/', ok_codes = {200: ''})

if __name__ == "__main__":
    testsuite.main()

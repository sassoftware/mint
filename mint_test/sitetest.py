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
import time

import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
import rephelp

from webunit import webunittest

class SiteTest(mint_rephelp.WebRepositoryHelper):
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

    def testEditUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        page = page.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'newpassword',
                              'password2': 'newpasswordasdf'})
        self.failIf('Passwords do not match.' not in page.body,
                    'Nonmatching passwords accepted.')
        page = page.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'new',
                              'password2': 'new'})
        self.failIf('Password must be 6 characters or longer.' not in page.body,
                    'Nonmatching passwords accepted.')
        page = page.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.post,
                              {'displayEmail': 'display@newemail.com',
                              'fullName': 'Foo B. Bar',
                              'blurb': 'blah blah blah'})
        cu = self.db.cursor()
        cu.execute("""SELECT displayEmail, fullName, blurb FROM users WHERE
                      userId=?""", userId)
        res = cu.fetchall()
        self.failUnless(res == [('display@newemail.com', 'Foo B. Bar', 
                                'blah blah blah')],
                        "User setting did not update properly.")
        page = page.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'newpassword',
                              'password2': 'newpassword'})
        page = self.webLogin('foouser', 'newpassword')
        self.failIf('logout' not in page.body,
                    'Failed to change user password.')

        # Disable changing user's email until we can mock out the other side.
        # Even if a mail server is available, we don't want to fire off real
        # mails at newemail.com (or example.com or wherever else) every time
        # we run the testsuite. -- gxti
        #
        #page = page.fetchWithRedirect('/userSettings')
        #page = page.postForm(2, page.fetch, 
        #                     {'email': 'foo@newemail.com'})
        #self.failIf('Please follow the directions in your confirmation email to complete the update process.' not in page.body,
        #            'Unable to update user e-mail.')

    def testAddMemberById(self):
        client, userId = self.quickMintUser('foouser','foopass')
        client2, userId2 = self.quickMintUser('baruser','barpass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN, 
                        shortname='foo', version="1.0", prodtype="Component")
        projectId2 = client2.newProject('Bar', 'bar', MINT_PROJECT_DOMAIN,
                        shortname='bar', version="1.0", prodtype="Component")
        page = self.webLogin('foouser', 'foopass')
        self.assertContent('/addMemberById?userId=%s&projectId=%s&level=0'\
                          % (userId2, projectId2),
                          content="Permission Denied",
                          code=[200])
        self.fetch('/addMemberById?userId=%s&projectId=%s&level=0' % (userId2, projectId))
        cu = self.db.cursor()
        cu.execute("""SELECT COUNT(*) FROM projectusers WHERE projectId=? AND
                      userId=?""", projectId, userId2)
        self.failUnless(cu.fetchone()[0], "Unable to add a new project member.")
        
    def testInvalidSearch(self):
        page = self.fetch('/search?type=Faketype&search=foobar',
                          ok_codes = [200])

        assert('Invalid search type specified.') in page.body

    def testCancelAccount(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        self.assertContent('/cancelAccount', 
                           content='Are you sure you want to close your account?',
                           code=[200])
        self.assertNotContent('/cancelAccount?confirmed=1', 
                           content='Are you sure you want to close your account?',
                           code=[301])

    def testGroupTroveSearch(self):
        if not self.mintCfg.rBuilderOnline:
            raise testsuite.SkipTestException("Test needs group builder, which has been disabled in non-rBO mode")
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        gt = client.createGroupTrove(projectId, 'group-blah', '1', 'testing', True)
        gt.addTrove('group-appliance-platform',
            '/blah.blah.blah@rpl:1/1.1.1-1-1', '', '', False, False, False)
        page = page.fetch('/project/foo/editGroup?id=%s' % gt.id)
        page = page.fetch('/search?type=Packages')
        self.failIf('only packages for rpl:1 branch' not in page.body, 
                    "Package search failed to limit search to rpl:1 branch")
    
    def testPackageSearchFormat(self):
        if not self.mintCfg.rBuilderOnline:
            raise testsuite.SkipTestException("Test needs group builder, which has been disabled in non-rBO mode")
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        hostname = 'foo'
        projectId = client.newProject('Foo', hostname, MINT_PROJECT_DOMAIN,
                        shortname=hostname, version="1.0", prodtype="Component")
        cu = self.db.cursor()
        for name in ('package1', 'package2', 'package3'):
            cu.execute("SELECT COALESCE(MAX(pkgId) + 1, 1) FROM PackageIndex")
            pkgId = cu.fetchone()[0]
            r = cu.execute("INSERT INTO PackageIndex VALUES(?, ?, ?, '/test.project.test@test:test/1.1-1-1', ?, 'test:test', 0)", (pkgId, projectId, name, MINT_PROJECT_DOMAIN))
        self.db.commit()
        self.failIf('<tr> <td> <a href="/repos/foo/troveInfo?t=package2;v=%2Ftest.project.test%40test%3Atest%2F1.1-1-1" class="mainSearchItem">package2</a> </td> <td> <a href="/project/foo/">Foo</a> </td> </tr>' not in ' '.join(self.fetch('/search?type=Packages').body.split()))
        gt = client.createGroupTrove(projectId, 'group-blah', '1', 'testing', True)
        gt.addTrove('group-core', '/blah.blah.blah@test:test/1.1.1-1-1', '', '', False, False, False)
        page = page.fetch('/project/foo/editGroup?id=%s' % gt.id)
        page = page.fetch('/search?type=Packages')
        self.failIf('Add to group-blah' not in page.body)

    def testBadCmd(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        self.assertRaises(webunittest.HTTPError, page.fetch, '/badcmd')

    def testProcessUserAction(self):
        client, userId = self.quickMintUser('foouser','foopass')
        adminClient, adminUserId = self.quickMintAdmin('adminuser','adminpass')
        page = self.webLogin('adminuser', 'adminpass')
        page = page.fetchWithRedirect('/processUserAction?userId=%s&operation=user_reset_password' % userId) 
        self.failIf('Password successfully reset for user foouser' not in page.body)
        page = page.fetchWithRedirect('/processUserAction?userId=%s&operation=user_cancel' % adminUserId) 
        self.failIf("You cannot close your account from this interface." not in page.body)
        page = page.fetchWithRedirect('/processUserAction?userId=%s&operation=user_promote_admin' % userId) 
        self.failIf("Promoted foouser to administrator." not in page.body)
        page = page.fetchWithRedirect('/processUserAction?userId=%s&operation=user_demote_admin' % userId) 
        self.failIf("Revoked administrative privileges for foouser" not in page.body)
        page = page.fetchWithRedirect('/processUserAction?userId=%s&operation=user_cancel' % userId) 
        self.failIf("Account deleted for user foouser" not in page.body)

if __name__ == "__main__":
    testsuite.main()

#!/usr/bin/python2.4
#
# Copyright (c) 2005-2007 rPath, Inc.
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

    def testApplianceSpotlight(self):
        adminClient, userId = self.quickMintAdmin('adminuser','adminpass')
        page = self.webLogin('adminuser', 'adminpass')
        
        self.assertContent('/applianceSpotlight', content='There are currently no appliances in the archive.  Please check back later.',
                           code = [200])

        end = time.strftime('%m/%d/%Y', time.gmtime(time.time() + 7*24*60*60))
        start = time.strftime('%m/%d/%Y', time.gmtime(time.time() - 7*24*60*60))
        adminClient.addSpotlightItem('Test Current', 'Description',
                                     'link', '', 0, 
                                     start,
                                     end)
        self.assertContent('/applianceSpotlight', 
                           content='There are currently no appliances in the archive.  Please check back later.',
                           code = [200])
        adminClient.addSpotlightItem('Test Item', 'Description', 'link', '',
                                     0, '1/1/1975', '1/2/1975')
        self.assertContent('/applianceSpotlight', 
                           content='Test Item',
                           code = [200])
        items = []
        for x in range(10):
            adminClient.addSpotlightItem('Test %d' % x, 'Description %d' % x,
                                         'link %d' % x, '', 0, 
                                         '2/%d/1990' % (x + 1),
                                         '2/%d/1990' % (x + 2))
        self.assertContent('/applianceSpotlight', 
                           content='Test 9',
                           code = [200])
        self.assertNotContent('/applianceSpotlight', 
                           content='Test 4',
                           code = [200])
        self.assertNotContent('/applianceSpotlight', 
                           content='apps/mint/images/prev.gif',
                           code = [200])
        self.assertContent('/applianceSpotlight', 
                           content='apps/mint/images/next.gif',
                           code = [200])
        self.assertContent('/applianceSpotlight?pageId=2', 
                           content='Test 3',
                           code = [200])
        self.assertContent('/applianceSpotlight?pageId=2', 
                           content='apps/mint/images/next.gif',
                           code = [200])
        self.assertContent('/applianceSpotlight?pageId=2', 
                           content='apps/mint/images/prev.gif',
                           code = [200])
        self.assertContent('/applianceSpotlight?pageId=3', 
                           content='Test Item',
                           code = [200])
        self.assertContent('/applianceSpotlight?pageId=3', 
                           content='apps/mint/images/prev.gif',
                           code = [200])
        self.assertNotContent('/applianceSpotlight?pageId=3', 
                           content='apps/mint/images/next.gif',
                           code = [200])
        adminClient.addUseItIcon(0, 'test.image', 'test.link')
        self.assertContent('/', 
                           content='test.link',
                           code = [200])
        for x in (1,2,3):
            adminClient.addUseItIcon(x, 'test%s.image' % x, 'test%s.link' % x)
        self.assertContent('/', 
                           content='test3.link',
                           code = [200])

        adminClient.addUseItIcon(4, 'test4.image', 'test4.link')
        self.assertContent('/', 
                           content='test4.link',
                           code = [200])

    def testEditUserSettings(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        page = page.fetch('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'newpassword',
                              'password2': 'newpasswordasdf'})
        self.failIf('Passwords do not match.' not in page.body,
                    'Nonmatching passwords accepted.')
        page = page.fetch('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'new',
                              'password2': 'new'})
        self.failIf('Password must be 6 characters or longer.' not in page.body,
                    'Nonmatching passwords accepted.')
        page = page.fetch('/userSettings')
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
        page = page.fetch('/userSettings')
        page = page.postForm(2, page.fetch, 
                              {'password1': 'newpassword',
                              'password2': 'newpassword'})
        page = self.webLogin('foouser', 'newpassword')
        self.failIf('logout' not in page.body,
                    'Failed to change user password.')

        page = page.fetchWithRedirect('/userSettings')
        page = page.postForm(2, page.fetch, 
                             {'email': 'foo@newemail.com'})
        self.failIf('Please follow the directions in your confirmation email to complete the update process.' not in page.body,
                    'Unable to update user e-mail.')

    def testAddMemberById(self):
        client, userId = self.quickMintUser('foouser','foopass')
        client2, userId2 = self.quickMintUser('baruser','barpass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        projectId2 = client2.newProject('Bar', 'bar', MINT_PROJECT_DOMAIN)
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
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        gt = client.createGroupTrove(projectId, 'group-blah', '1', 'testing', True)
        gt.addTrove('group-core', '/blah.blah.blah@rpl:1/1.1.1-1-1', '', '', False, False, False)
        page = page.fetch('/project/foo/editGroup?id=%s' % gt.id)
        page = page.fetch('/search?type=Packages')
        self.failIf('only packages for rpl:1 branch' not in page.body, 
                    "Package search failed to limit search to rpl:1 branch")
    
    def testPackageSearchFormat(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        projectId = client.newProject('Foo', 'foo', MINT_PROJECT_DOMAIN)
        cu = self.db.cursor()
        for name in ('package1', 'package2', 'package3'):
            cu.execute("SELECT IFNULL(MAX(pkgId) + 1, 1) FROM PackageIndex")
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

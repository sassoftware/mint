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
import time

import mint_rephelp
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN
import rephelp

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

if __name__ == "__main__":
    testsuite.main()

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
import xmlrpclib

from mint_test import mint_rephelp
from mint_rephelp import MINT_PROJECT_DOMAIN

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

    def testBadCmd(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')
        self.assertRaises(webunittest.HTTPError, page.fetch, '/badcmd')

    def testPysidXmlRpcAuth(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        cookie = page.cookies[page.server]['/']['pysid']

        conn = xmlrpclib.ServerProxy("%s://%s:%s/xmlrpc-private/" % (
            page.protocol, page.server, page.port),
            transport = Transport("pysid=%s" % cookie.value))
        ret = conn.checkAuth('RBUILDER_CLIENT:8')
        self.failIf(ret[0])
        self.failUnlessEqual(ret[1].get('username'), 'foouser')
        self.failUnlessEqual(ret[1].get('admin'), False)
        self.failUnlessEqual(ret[1].get('displayEmail'), 'test at example.com')
        self.failUnlessEqual(ret[1].get('authorized'), True)

    def testPysidXmlRpcAuthBad(self):
        client, userId = self.quickMintUser('foouser','foopass')
        page = self.webLogin('foouser', 'foopass')

        cookie = "A" * 32

        conn = xmlrpclib.ServerProxy("%s://%s:%s/xmlrpc-private/" % (
            page.protocol, page.server, page.port),
            transport = Transport("pysid=%s" % cookie))
        ret = conn.checkAuth('RBUILDER_CLIENT:8')
        self.failIf(ret[0])
        # checkAuth allows anonymous access.
        self.failUnlessEqual(ret[1], {'userId': -1, 'authorized': False})

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

class Transport(xmlrpclib.Transport):
    "Cookie-enabled transport"
    def __init__(self, cookie):
        if hasattr(xmlrpclib.Transport, '__init__'):
            xmlrpclib.Transport.__init__(self)
        self.cookie = cookie

    def send_user_agent(self, connection):
        xmlrpclib.Transport.send_user_agent(self, connection)
        connection.putheader('Cookie', self.cookie)

if __name__ == "__main__":
    testsuite.main()

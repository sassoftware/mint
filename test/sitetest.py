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


if __name__ == "__main__":
    testsuite.main()

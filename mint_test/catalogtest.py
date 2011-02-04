#!/usr/bin/python
#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
testsuite.setup()

import boto
import cPickle
import os
import urlparse

from mint_test import mint_rephelp
import ec2test
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN

from catalogService import handler, storage
from catalogService.rest.database import RestDatabase

class WebPageTest(mint_rephelp.WebRepositoryHelper):
    def setUp(self):
        self.mock(boto, 'connect_ec2', ec2test.getFakeEC2Connection)
        mint_rephelp.WebRepositoryHelper.setUp(self)

    def _checkRedirect(self, url, expectedRedirect, code=301):
        page = self.assertCode(url, code)
        redirectUrl = page.headers.getheader('location')
        self.failUnlessEqual(redirectUrl, expectedRedirect,
                "Expected redirect to %s, got %s" % \
                        (expectedRedirect, redirectUrl))


    def testBasicAuth(self):
        username, password = 'foouser', 'foopass'
        client, userId = self.quickMintUser(username, password)
        url = "http://%s:%s@%s/catalog/clouds" % (username, password,
            client._cfg.siteHost)
        from restlib import client
        cli = client.Client(url)
        cli.connect()
        resp = cli.request("GET")
        self.failUnlessEqual(resp.status, 200)
        data = resp.read()
        self.failUnless('<cloudTypes' in data, data)

    def testBasicAuthFail(self):
        username, password = 'foouser', 'foopass'
        client, userId = self.quickMintUser(username, password)
        url = "http://%s/catalog/clouds" % (client._cfg.siteHost, )
        from restlib import client
        cli = client.Client(url)
        cli.connect()

        tests = [
            (None, 401, "Unauthorized"),
            ('NoSuchAuthMethodExists aa', 401, "Unauthorized"),
            ('Basic', 401, "Unauthorized"),
            ('Basic a', 400,
                "AuthHeaderError: Your authentication header could not be decoded"),
            ('Basic YQ==', 400,
                "AuthHeaderError: Your authentication header could not be decoded"),
        ]
        errMsgTmpl = """\
<?xml version='1.0' encoding='UTF-8'?>
<fault>
  <code>%s</code>
  <message>%s</message>
</fault>
"""
        for h, errCode, errMsg in tests:
            headers = dict()
            if h:
                headers['Authorization'] = h
            err = self.failUnlessRaises(client.ResponseError,
                cli.request, "GET", headers = headers)
            self.failUnlessEqual(err.status, errCode)
            self.failUnlessEqual(err.contents, errMsgTmpl % (errCode, errMsg))

    def testGetImagesNoCred(self):
        # Enable EC2 in rbuilder
        restdb = self.openRestDatabase()
        restdb.targetMgr.addTarget('ec2', 'aws', dict(
            ec2PublicKey = 'Public Key',
            ec2PrivateKey = 'Private Key',
            ec2AccountId = '867-5309',))
        restdb.commit()

        client, userId = self.quickMintUser('foouser', 'foopass')
        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/catalog/clouds/ec2/instances/aws/images?_method=GET', ok_codes = [400])
        self.assertEquals(page.headers['content-type'], 'application/xml')
        self.assertEquals(page.body, 
                "<?xml version='1.0' encoding='UTF-8'?>\n<fault>\n  "
                "<code>400</code>\n  <message>Target credentials not set for "
                "user</message>\n</fault>\n")

    def openRestDatabase(self):
        restdb = mint_rephelp.WebRepositoryHelper.openRestDatabase(self)
        restdb = RestDatabase(restdb.cfg, restdb.db)
        return restdb

    def testGetImagesNoSession(self):
        restdb = self.openRestDatabase()
        restdb.targetMgr.addTarget('ec2', 'aws', dict(
            ec2PublicKey = 'Public Key',
            ec2PrivateKey = 'Private Key',
            ec2AccountId = '867-5309',))
        restdb.commit()
        page = self.fetch('/catalog/clouds/ec2/instances/aws/images?_method=GET', ok_codes = [401])

    def testEnumerateNoImages(self):
        raise testsuite.SkipTestException("This test case will really try to talk to EC2")
        client, userId = self.quickMintUser('foouser', 'foopass')
        client.setEC2CredentialsForUser(userId, 'testAccountNumber',
                'testPublicKey', 'testSecretAccessKey', True)

        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/catalog/clouds/ec2/instances/aws/images?_method=GET', ok_codes = [400])
        self.assertEquals(page.headers['content-type'], 'application/xml')
        self.assertEquals(page.body,
                '<fault code="400">Cloud credentials are not set in rBuilder</fault>')

    def testEnumerateNoVwsImages(self):
        # we don't need special remote credentials to see rBuilder images
        client, userId = self.quickMintUser('foouser', 'foopass')
        page = self.webLogin('foouser', 'foopass')

        raise testsuite.SkipTestException('We need a real cloud or a way to mock')
        page = self.fetch('/catalog/clouds/vws/cloudid/images?_method=GET')
        self.assertEquals(page.headers['content-type'], 'application/xml')
        self.assertEquals(page.body, "<?xml version='1.0' encoding='UTF-8'?>\n<images/>\n")


if __name__ == "__main__":
    testsuite.main()

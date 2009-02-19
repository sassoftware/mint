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

import mint_rephelp
import ec2test
from mint_rephelp import MINT_HOST, MINT_PROJECT_DOMAIN, MINT_DOMAIN

from catalogService import handler, storage

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


    @staticmethod
    def normalizeXML(data):
        """lxml will produce the header with single quotes for its attributes,
        while xmllint uses double quotes. This function normalizes the data"""
        return data.replace(
            "<?xml version='1.0' encoding='UTF-8'?>",
            '<?xml version="1.0" encoding="UTF-8"?>').strip()

    def assertXMLEquals(self, first, second):
        self.failUnlessEqual(self.normalizeXML(first),
                             self.normalizeXML(second))

    def testGetImagesNoCred(self):
        # Enable EC2 in rbuilder
        storagePath = os.path.join(self.mintCfg.dataPath,
            'catalog', 'configuration', 'ec2', 'aws')
        store = storage.DiskStorage(storage.StorageConfig(storagePath))
        store.set("enabled", 1)

        client, userId = self.quickMintUser('foouser', 'foopass')
        page = self.webLogin('foouser', 'foopass')

        page = self.fetch('/catalog/clouds/ec2/instances/aws/images?_method=GET', ok_codes = [400])
        self.assertEquals(page.headers['content-type'], 'application/xml')
        self.assertEquals(page.body, 
                "<?xml version='1.0' encoding='UTF-8'?>\n<fault>\n  "
                "<code>400</code>\n  <message>Target credentials not set for "
                "user</message>\n</fault>\n")

    def testGetImagesNoSession(self):
        page = self.fetch('/catalog/clouds/ec2/instances/aws/images?_method=GET', ok_codes = [403])

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

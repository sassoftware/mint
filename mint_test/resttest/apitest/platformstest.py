#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import testsetup

import os
import re
import time

from conary.lib import util
from mint import buildtypes

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class PlatformTest(restbase.BaseRestTest):
    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.setupProduct()

    def testGetPlatforms(self):
        uriTemplate = 'platforms'
        uri = uriTemplate
        client = self.getRestClient(uri)
        response = client.request('GET')
        # This is less than helpful.
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<platformsNames/>
"""
        self.failUnlessEqual(response.read(),
             exp % dict(port = client.port, server = client.server))

if __name__ == "__main__":
        testsetup.main()

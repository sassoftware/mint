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

from conary import conaryclient
from conary import constants as conaryConstants
from conary.lib import util
from mint import buildtypes
from mint import constants

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class SiteTest(restbase.BaseRestTest):
    def testGetInfo(self):
        uriTemplate = ''
        uri = uriTemplate
        client = self.getRestClient()
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<rbuilderStatus id="http://%(server)s:%(port)s/api">
  <version>%(version)s</version>
  <conaryVersion>%(conaryversion)s</conaryVersion>
  <isRBO>false</isRBO>
  <identity>
    <rbuilderId></rbuilderId>
    <serviceLevel status="Unknown" daysRemaining="-1" expired="true" limited="true"/>
    <registered>false</registered>
  </identity>
  <products href="http://%(server)s:%(port)s/api/products/"/>
  <users href="http://%(server)s:%(port)s/api/users/"/>
  <platforms href="http://%(server)s:%(port)s/api/platforms"/>
</rbuilderStatus>
"""
        self.failUnlessEqual(response,
             exp % dict(port = client.port, server = client.server,
                         version=constants.mintVersion,
                         conaryversion=conaryConstants.version))

if __name__ == "__main__":
        testsetup.main()

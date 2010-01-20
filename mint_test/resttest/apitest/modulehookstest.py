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

from rpath_proddef import api1 as proddef

import restbase
from restlib import client as restClient
ResponseError = restClient.ResponseError

class ModuleHooksTest(restbase.BaseRestTest):

    def setUp(self):
        restbase.BaseRestTest.setUp(self)
        self.f1 = open('/tmp/test1.swf','w')
        self.f2 = open('/tmp/test2.swf','w')
        
    def tearDown(self):
        os.remove(self.f1.name)
        os.remove(self.f2.name)

    def testGetInfo(self):
        uriTemplate = '/moduleHooks'
        uri = uriTemplate
        client = self.getRestClient()
        self.mintCfg.moduleHooksDir = '/tmp'
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<moduleHooks>
  <moduleHook>
    <url>hooks/test1.swf</url>
  </moduleHook>
  <moduleHook>
    <url>hooks/test2.swf</url>
  </moduleHook>
</moduleHooks>
"""
        self.assertBlobEquals(response,
             exp % dict(port = client.port, server = client.server,
                         version=constants.mintVersion,
                         conaryversion=conaryConstants.version,
                         proddefVer=proddef.BaseDefinition.version))

if __name__ == "__main__":
        testsetup.main()

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
        self.f1 = open('/%s/test1.swf' % self.tmpDir,'w')
        self.f2 = open('/%s/test2.swf' % self.tmpDir,'w')
        
    def tearDown(self):
        os.remove(self.f1.name)
        os.remove(self.f2.name)

    def testGetInfo(self):
        uriTemplate = '/moduleHooks'
        uri = uriTemplate
        client = self.getRestClient()
        self.mintCfg.moduleHooksDir = self.tmpDir
        response = client.call('GET', uri, convert=False)[1]
        self.failUnlessEqual(len(response.moduleHooks), 2)

if __name__ == "__main__":
        testsetup.main()

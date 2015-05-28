#!/usr/bin/python
#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


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

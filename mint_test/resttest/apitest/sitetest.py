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
from rmake import constants as rmakeConstants

from rpath_proddef import api1 as proddef

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
  <rmakeVersion>%(rmakeversion)s</rmakeVersion>
  <userName>someuser</userName>
  <hostName>%(hostname)s</hostName>
  <isRBO>false</isRBO>
  <isExternalRba>false</isExternalRba>
  <accountCreationRequiresAdmin>false</accountCreationRequiresAdmin>
  <identity>
    <rbuilderId></rbuilderId>
    <serviceLevel status="Unknown" daysRemaining="-1" expired="false" limited="false"/>
    <registered>true</registered>
  </identity>
  <products href="http://%(server)s:%(port)s/api/products/"/>
  <users href="http://%(server)s:%(port)s/api/users/"/>
  <platforms href="http://%(server)s:%(port)s/api/platforms/"/>
  <registration href="http://%(server)s:%(port)s/api/registration"/>
  <reports href="http://%(server)s:%(port)s/api/reports/"/>
  <inventory href="http://%(server)s:%(port)s/api/inventory/"/>
  <query_sets href="http://localhost:8000/api/query_sets/"/>
  <packages href="http://localhost:8000/api/packages/"/>
  <moduleHooks href="http://%(server)s:%(port)s/api/moduleHooks/"/>
  <maintMode>false</maintMode>
  <proddefSchemaVersion>%(proddefVer)s</proddefSchemaVersion>
  <inventoryConfigurationEnabled>true</inventoryConfigurationEnabled>
  <imageImportEnabled>true</imageImportEnabled>
</rbuilderStatus>
"""
        self.assertBlobEquals(response,
             exp % dict(port = client.port, server = client.server,
                         version=constants.mintVersion,
                         conaryversion=conaryConstants.changeset,
                         rmakeversion=rmakeConstants.changeset,
                         hostname=os.uname()[1],
                         proddefVer=proddef.BaseDefinition.version))

if __name__ == "__main__":
        testsetup.main()

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

    def testGetUsersInfo(self):
        self.setupReleases()
        uriTemplate = 'users'
        uri = uriTemplate
        username = 'adminuser'
        client = self.getRestClient(username=username)
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<users>
  <user id="http://%(server)s:%(port)s/api/users/%(username)s">
    <userId>1</userId>
    <username>adminuser</username>
    <fullName>Full Name</fullName>
    <email>%(username)s@foo.com</email>
    <displayEmail>%(displayname)s@foo.com</displayEmail>
    <blurb></blurb>
    <active>true</active>
    <timeCreated></timeCreated>
    <timeAccessed></timeAccessed>
    <products href="http://%(server)s:%(port)s/api/users/%(username)s/products"/>
  </user>
</users>
"""
        for pat in [ "timeCreated", "timeAccessed" ]:
            response = re.sub("<%s>.*</%s>" % (pat, pat),
                          "<%s></%s>" % (pat, pat),
                          response)
        self.assertBlobEquals(response,
             exp % dict(port = client.port, server = client.server,
                         username = username, displayname = '%s'))

    def testGetUsersProductsInfo(self):
        self.setupReleases()
        username = 'adminuser'
        uri = 'users/%s/products' % username
        client = self.getRestClient(username=username)
        req, response = client.call('GET', uri, convert=True)
        exp = """\
<?xml version='1.0' encoding='UTF-8'?>
<members>
  <member id="">
    <hostname>testproject</hostname>
    <productUrl href="http://localhost:8000/api/products/testproject"/>
    <userUrl href="http://%(server)s:%(port)s/api/users/%(username)s"/>
    <username>adminuser</username>
    <level>Owner</level>
  </member>
</members>
"""
        for pat in [ "timeCreated", "timeAccessed" ]:
            response = re.sub("<%s>.*</%s>" % (pat, pat),
                          "<%s></%s>" % (pat, pat),
                          response)
        self.assertBlobEquals(response,
             exp % dict(port = client.port, server = client.server,
                         username = username, displayname = '%s'))


if __name__ == "__main__":
        testsetup.main()

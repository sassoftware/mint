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


import re
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
  <user id="http://%(server)s:%(port)s/api/users/mintauth">
    <userId>1</userId>
    <username>mintauth</username>
    <fullName>Internal Super-User</fullName>
    <active>true</active>
    <products href="http://%(server)s:%(port)s/api/users/mintauth/products"/>
  </user>
  <user id="http://%(server)s:%(port)s/api/users/%(username)s">
    <userId>2</userId>
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

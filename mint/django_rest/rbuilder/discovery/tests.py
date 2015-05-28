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
from lxml import etree
from xobj import xobj
from rpath_proddef.api1 import ProductDefinition

from mint.django_rest.rbuilder.inventory.tests import XMLTestCase

class VersionsTestCase(XMLTestCase):
    def toXObj(self, xml):
        xobjModel = xobj.parse(xml)
        root_name = etree.XML(xml).tag
        return getattr(xobjModel, root_name)

    def testVersions(self):
        response = self._get('/api')
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, """\
<api>
  <api_versions>
    <api_version description="rBuilder REST API version 1" id="http://testserver/api/v1" name="v1"/>
  </api_versions>
</api>""")

    def _mockConfigInfo(self):
        from mint import constants
        from conary import constants as conaryConstants
        from rmake import constants as rmakeConstants
        self.mock(constants, 'mintVersion', 'mint-version-42')
        self.mock(conaryConstants, 'changeset', 'conary-version-42')
        self.mock(rmakeConstants, 'changeset', 'rmake-version-42')
        self.mock(os, 'uname', lambda: ('Lunix', 'superduper.example.com', '1.1'))

    def testVersion(self):
        self._mockConfigInfo()
        response = self._get('/api/v1')
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, """\
<api_version id="http://testserver/api/v1" name="v1" description="rBuilder REST API version 1">
  <config_info>
    <account_creation_requires_admin>false</account_creation_requires_admin>
    <hostname>superduper.example.com</hostname>
    <inventory_configuration_enabled>true</inventory_configuration_enabled>
    <is_external_rba>false</is_external_rba>
    <maintenance_mode>false</maintenance_mode>
    <rbuilder_id />
  </config_info>
  <grants id="http://testserver/api/v1/rbac/grants"/>
  <inventory id="http://testserver/api/v1/inventory"/>
  <images id="http://testserver/api/v1/images"/>
  <jobs id="http://testserver/api/v1/jobs"/>
  <module_hooks id="http://testserver/api/v1/module_hooks"/>
  <packages id="http://testserver/api/v1/packages"/>
  <permissions id="http://testserver/api/v1/rbac/permissions"/>
  <platforms id="http://testserver/api/platforms"/>
  <products id="http://testserver/api/products"/>
  <projects id="http://testserver/api/v1/projects"/>
  <project_branches id="http://testserver/api/v1/project_branches"/>
  <project_branch_stages id="http://testserver/api/v1/project_branch_stages"/>
  <query_sets id="http://testserver/api/v1/query_sets"/>
  <rbac id="http://testserver/api/v1/rbac"/>
  <roles id="http://testserver/api/v1/rbac/roles"/>
  <users id="http://testserver/api/v1/users"/>
  <session id="http://testserver/api/v1/session"/>
  <targets id="http://testserver/api/v1/targets"/>
  <version_info>
    <conary_version>conary-version-42</conary_version>
    <product_definition_schema_version>%(proddef_version)s</product_definition_schema_version>
    <rbuilder_version>mint-version-42</rbuilder_version>
    <rmake_version>rmake-version-42</rmake_version>
  </version_info>
</api_version>""" % dict(
    proddef_version=ProductDefinition.version,
    ))

    def testAccessViaRepeaterIsHttps(self):
        # RCE-2021
        self._mockConfigInfo()
        response = self._get('/api',
            headers={'X-rPath-Repeater' : 'does not matter'})
        self.failUnlessEqual(response.status_code, 200)
        self.assertXMLEquals(response.content, """\
<api>
  <api_versions>
    <api_version description="rBuilder REST API version 1" id="https://testserver:80/api/v1" name="v1"/>
  </api_versions>
</api>""")

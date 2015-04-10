#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
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
  <xml_resources id="/api/v1/xml_resources">
    <schemas>
      <rpath_configurator_2_0 id="/schemas/rpath-configurator-2.0.xsd" name="rpath-configurator-2.0.xsd"/>
      <rpath_descriptor_1_1 id="/schemas/descriptor-1.1.xsd" name="descriptor-1.1.xsd"/>
    </schemas>
  </xml_resources>
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

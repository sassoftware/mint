#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import os

from conary import constants as conaryConstants
from rmake import constants as rmakeConstants
from rpath_proddef import api1 as proddef
from mint import constants

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.discovery import models
exposed = basemanager.exposed

class DiscoveryManager(basemanager.BaseManager):
    @exposed
    def getApi(self):
        api = models.Api()
        return api

    @exposed
    def getApiVersionInfo(self):
        apiVersion = models.ApiVersion()
        v1 = models.Api.Constants.v1
        apiVersion.id = v1.id
        apiVersion.name = v1.name
        apiVersion.description = v1.description
        apiVersion.config_info = ci = models.ConfigInfo()
        apiVersion.version_info = vi = models.VersionInfo()

        vi.rbuilder_version = constants.mintVersion
        vi.conary_version = conaryConstants.changeset
        vi.rmake_version = rmakeConstants.changeset
        vi.product_definition_schema_version = proddef.BaseDefinition.version

        ci.hostname = os.uname()[1]
        ci.is_external_rba = self._bool(self.cfg.rBuilderExternal)
        ci.account_creation_requires_admin = self._bool(self.cfg.adminNewUsers)
        ci.maintenance_mode = 'false'
        ci.inventory_configuration_enabled = self._bool(self.cfg.inventoryConfigurationEnabled)
        ci.rbuilder_id = self._getRbuilderId()
        return apiVersion

    def _getRbuilderId(self):
        return ''

    @classmethod
    def _bool(cls, val):
        if val is None:
            return None
        return str(bool(val)).lower()

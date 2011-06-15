#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from xobj import xobj
from mint.django_rest.rbuilder import modellib

class Version(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'version',
        attributes=dict(id=str, name=str, description=str))
    view_name = 'API'
    id = modellib.SyntheticField()
    name = modellib.SyntheticField()
    description = modellib.SyntheticField()

    def __init__(self, id=None, name=None, description=None):
        self.id = id
        self.name = name
        self.description = description

    def get_url_key(self):
        # We construct the URL by appending the ID to /api
        # This is because we don't have a view to resolve it for us
        return []

    def get_absolute_url(self, request):
        return "%s/%s" % (modellib.XObjIdModel.get_absolute_url(self, request),
            self.id)

class Versions(modellib.XObjModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'versions')
    list_fields = ['version']
    version = []

class Api(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'api')
    versions = Versions

    def __init__(self):
        self.versions = Versions()
        self.versions.version.append(
            Version(id='v1', name='v1', description='rBuilder REST API version 1'))

class VersionInfo(modellib.XObjIdModel):
    class Meta:
        abstract = True
    conary_version = modellib.SyntheticField()
    rbuilder_version = modellib.SyntheticField()
    rmake_version = modellib.SyntheticField()
    product_definition_schema_version = modellib.SyntheticField()

class ConfigInfo(modellib.XObjIdModel):
    class Meta:
        abstract = True

    account_creation_requires_admin = modellib.SyntheticField()
    hostname = modellib.SyntheticField()
    image_import_enabled = modellib.SyntheticField()
    inventory_configuration_enabled = modellib.SyntheticField()
    is_external_rba = modellib.SyntheticField()
    maintenance_mode = modellib.SyntheticField()
    rbuilder_id = modellib.SyntheticField()

class ApiVersion(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'api_version', attributes=dict(id=str))
    view_name = 'APIVersion'

    changelogs = modellib.HrefField("changelogs")
    inventory = modellib.HrefField("inventory")
    jobs = modellib.HrefField("jobs")
    module_hooks = modellib.HrefField("module_hooks")
    notices = modellib.HrefField("notices")
    packages = modellib.HrefField("packages")
    platforms = modellib.HrefField("../platforms")
    products = modellib.HrefField("../products")
    projects = modellib.HrefField("../projects")
    query_sets = modellib.HrefField("query_sets")
    reports = modellib.HrefField("reports")
    users = modellib.HrefField("users")
    session = modellib.HrefField("session")
    config_info = ConfigInfo()
    version_info = VersionInfo()

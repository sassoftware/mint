from mint.django_rest.rbuilder.platforms import fields
from xobj import xobj
from mint.django_rest.rbuilder import modellib
 

class Status(modellib.XObjModel):
    class Meta:
        abstract = True
        
    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField()
    
    _xobj = xobj.XObjMetadata(tag='status')
    
    
class SourceStatus(Status):
    class Meta:
        name = 'content_source_status'
        
    _xobj = xobj.XObjMetadata(tag='source_status')
    
    
class PlatformSourceStatus(Status):
    class Meta:
        name = 'platform_source_status'
    
    _xobj = xobj.XObjMetadata(tag='platform_source_status')
    
    
class Source(modellib.XObjIdModel):
    class Meta:
        abstract = True
        name = 'content_source'
    
    content_source_id = fields.CharField(primary_key=True)
    name = fields.CharField()
    short_name = fields.CharField(unique=True)
    default_source = fields.BooleanField()
    order_index = fields.IntegerField()
    content_source_type = fields.CharField()
    enabled = fields.BooleanField()
    content_source_status = fields.UrlField()
    resource_errors = fields.UrlField()
    # id = fields.AbsoluteUrlField()
    
    _xobj = xobj.XObjMetadata(tag='source')
    
    
class NuSource(Source):
    class Meta:
        name = 'content_source'
    user_name = fields.CharField()
    passwd = fields.CharField()

    _xobj = xobj.XObjMetadata(tag='nu_source')

    
class SmtSource(Source):
    class Meta:
        name = 'content_source'
        
    user_name = fields.CharField()
    passwd = fields.CharField()
    source_url = fields.CharField()
    
    _xobj = xobj.XObjMetadata(tag='smt_source')
    
    
class RhnSource(Source):
    class Meta:
        name = 'content_source'
        
    user_name = fields.CharField()
    passwd = fields.CharField()
    
    _xobj = xobj.XObjMetadata(tag='rhn_source')
    
    
class SatelliteSource(Source):
    class Meta:
        name = 'content_source'
        
    user_name = fields.CharField()
    passwd = fields.CharField()
    source_url = fields.CharField()
    
    _xobj = xobj.XObjMetadata(tag='satellite_source')


class SourceTypes(modellib.Collection):
    list_fields = ['source_type']
    _xobj = xobj.XObjMetadata(tag='source_types')
    
    
class SourceType(modellib.XObjIdModel):
    class Meta:
        name = 'content_source_type'
        
    content_source_type = fields.CharField()
    required = fields.BooleanField()
    singleton = fields.BooleanField()
    instances = fields.UrlField()
    config_descriptor = fields.UrlField()
    status_test = fields.UrlField()
    # id = fields.AbsoluteUrlField()
    
    _xobj = xobj.XObjMetadata(tag='source_type')
    
    
class ContentSourceInstances(modellib.Collection):
    class Meta:
        name = 'content_sources'
    list_fields = ['source']
    _xobj = xobj.XObjMetadata(tag='content_source_instances')

      
class ContentSources(modellib.Collection):
    list_fields = ['source_type']
    _xobj = xobj.XObjMetadata(tag='content_sources')
    
    
class SourceInstances(modellib.Collection):
    class Meta:
        name = 'instances'
    list_fields = ['source']
    _xobj = xobj.XObjMetadata(tag='source_instances')


class PlatformVersions(modellib.Collection):
    list_fields = ['platform_version']
    _xobj = xobj.XObjMetadata(tag='platform_versions')


class PlatformVersion(modellib.XObjIdModel):
    class Meta:
        name = 'platform_version'
    name = fields.CharField()
    version = fields.CharField()
    revision = fields.CharField()
    label = fields.CharField()
    ordering = fields.CharField()
    platform_id = fields.CharField()
    # id = fields.AbsoluteUrlField(isAttribute=True)
    _xobj = xobj.XObjMetadata(tag='platform_version')
    
    
class EmptyPlatformVersions(modellib.Collection):
    class Meta:
        name = 'platform_version'
    _xobj = xobj.XObjMetadata(tag='EmptyPlatformVersions')

    
class Platforms(modellib.Collection):
    list_fields = ['platform']
    _xobj = xobj.XObjMetadata(tag='platforms')


class Platform(modellib.XObjIdModel):
    platform_id = fields.CharField()
    platform_trove_name = fields.CharField()
    repository_host_name = fields.CharField()
    label = fields.CharField()
    platform_version = fields.CharField()
    product_version = fields.CharField()
    platform_name = fields.CharField()
    platform_usage_terms = fields.CharField()
    mode = fields.CharField()
    enabled = fields.BooleanField()
    configurable = fields.BooleanField()
    abstract = fields.BooleanField()
    mirror_permission = fields.BooleanField()
    # repository_url = _RepositoryUrlField()
    # contentSources = fields.ModelField(SourceRefs)
    content_sources = fields.UrlField()
    platform_type = fields.CharField()
    platform_status = fields.UrlField()
    # contentSourceTypes = fields.ModelField(SourceTypeRefs)
    content_source_types = fields.UrlField()
    load = fields.UrlField()
    image_type_definitions = fields.UrlField()
    is_platform = fields.BooleanField()
    platform_versions = fields.UrlField()
    # id = fields.AbsoluteUrlField(isAttribute=True)
    
    _xobj = xobj.XObjMetadata(tag='platform')
      
      
class ProductPlatform(Platform):
    class Meta(object):
        name = 'platform'

    host_name = fields.CharField()
    _xobj = xobj.XObjMetadata(tag='product_platform')
    
    
class PlatformLoadStatusStub(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(tag='platform_load_status_stub')
    # id = fields.AbsoluteUrlField(isAttribute=True)
    
    
class PlatformLoad(modellib.XObjIdModel):
    load_uri = fields.CharField()
    job_id = fields.CharField()
    platform_id = fields.IntegerField()
    job = fields.UrlField()
    
    _xobj = xobj.XObjMetadata(tag='platform_load')
    
    
class PlatformLoadStatus(modellib.XObjIdModel):
    code = fields.IntegerField()
    message = fields.CharField()
    is_final = fields.BooleanField()

    _xobj = xobj.XObjMetadata(tag='platform_load_status')
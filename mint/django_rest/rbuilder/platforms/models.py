from django.db import models
from xobj import xobj
from mint.django_rest.rbuilder import modellib
    
     
class Status(modellib.XObjModel):
    connected = models.BooleanField()
    valid = models.BooleanField()
    message = models.CharField()
    
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
        name = 'content_source'
    
    content_source_id = models.CharField()
    name = models.CharField()
    short_name = models.CharField()
    default_source = models.BooleanField()
    order_index = models.IntegerField()
    content_source_type = models.CharField()
    enabled = models.BooleanField()
    content_source_status = models.UrlField()
    resource_errors = models.UrlField()
    # id = models.AbsoluteUrlField()
    
    _xobj = xobj.XObjMetadata(tag='source')
    
    
class NuSource(Source):
    class Meta:
        name = 'content_source'
    user_name = models.CharField()
    passwd = models.CharField()

    _xobj = xobj.XObjMetadata(tag='nu_source')

    
class SmtSource(Source):
    class Meta:
        name = 'content_source'
    user_name = models.CharField()
    passwd = models.CharField()
    source_url = models.CharField()
    
    _xobj = xobj.XObjMetadata(tag='smt_source')
    
    
class RhnSource(Source):
    class Meta:
        name = 'content_source'
    user_name = models.CharField()
    passwd = models.CharField()
    
    _xobj = xobj.XObjMetadata(tag='rhn_source')
    
    
class SatelliteSource(RhnSource):
    class Meta:
        name = 'content_source'
    source_url = models.CharField()
    
    _xobj = xobj.XObjMetadata(tag='satellite_source')


class SourceTypes(modellib.Collection):
    list_fields = ['source_type']
    _xobj = xobj.XObjMetadata(tag='source_types')
    
    
class SourceType(modellib.XObjIdModel):
    class Meta:
        name = 'content_source_type'
        
    content_source_type = models.CharField()
    required = models.BooleanField()
    singleton = models.BooleanField()
    instances = models.UrlField()
    config_descriptor = models.UrlField()
    status_test = models.UrlField()
    # id = models.AbsoluteUrlField()
    
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
    name = models.CharField()
    version = models.CharField()
    revision = models.CharField()
    label = models.CharField()
    ordering = models.CharField()
    _platformId = models.CharField()
    # id = models.AbsoluteUrlField(isAttribute=True)
    _xobj = xobj.XObjMetadata(tag='platform_version')
    
    
class EmptyPlatformVersions(modellib.Collection):
    class Meta:
        name = 'platform_version'
    _xobj = xobj.XObjMetadata(tag='EmptyPlatformVersions')

    
class Platforms(modellib.Collection):
    list_fields = ['platform']
    _xobj = xobj.XObjMetadata(tag='platforms')


class Platform(modellib.XObjIdModel):
    platform_id = models.CharField()
    platform_trove_name = models.CharField()
    repository_host_name = models.CharField()
    label = models.CharField()
    platform_version = models.CharField()
    product_version = models.CharField()
    platform_name = models.CharField()
    platform_usage_terms = models.CharField()
    mode = models.CharField()
    enabled = models.BooleanField()
    configurable = models.BooleanField()
    abstract = models.BooleanField()
    mirror_permission = models.BooleanField()
    repository_url = _RepositoryUrlField()
    # contentSources = models.ModelField(SourceRefs)
    content_sources = models.UrlField()
    platform_type = models.CharField()
    platform_status = models.UrlField()
    # contentSourceTypes = models.ModelField(SourceTypeRefs)
    content_source_types = models.UrlField()
    load = models.UrlField()
    image_type_definitions = models.UrlField()
    is_platform = models.BooleanField()
    platform_versions = models.UrlField()
    # id = models.AbsoluteUrlField(isAttribute=True)
    
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
    load_uri = models.CharField()
    job_id = models.CharField()
    platform_id = models.IntegerField()
    job = models.UrlField()
    
    _xobj = xobj.XObjMetadata(tag='platform_load')
    
    
class PlatformLoadStatus(modellib.XObjIdModel):
    code = models.IntegerField()
    message = models.CharField()
    is_final = models.BooleanField()

    _xobj = xobj.XObjMetadata(tag='platform_load_status')

    
# class PlatformArchitecture(Architecture):
#     pass
#     
# class PlatformFlavorSet(FlavorSet):
#     pass
#     
# class PlatformContainerFormat(ContainerFormate):
#     pass
#     
# class PlatformBuildTemplates(BuildTemplates):
#     pass
#     
# class PlatformBuildTemplate(BuildTemplate):
#     pass
#
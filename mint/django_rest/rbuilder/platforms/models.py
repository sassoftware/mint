#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.rbuilder.platforms import fields
from xobj import xobj
from mint.django_rest.rbuilder import modellib
import sys


class AbstractSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    content_source_id = models.AutoField(primary_key=True)
    name = fields.CharField(max_length=1026)
    short_name = fields.CharField(max_length=1026, unique=True)
    default_source = fields.BooleanField()
    order_index = fields.IntegerField()
    content_source_type = models.ForeignKey('SourceType')
    enabled = fields.BooleanField()
    content_source_status = models.ForeignKey('SourceStatus')
    # resource_errors = fields.UrlField() # what the heck does this go to
    

class AbstractStatus(modellib.XObjIdModel):
    class Meta:
        abstract = True

    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField(max_length=1026)


class AbstractPlatform(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    platform_id = models.AutoField(primary_key=True)
    platform_trove_name = fields.CharField(max_length=1026)
    repository_host_name = fields.CharField(max_length=1026)
    label = fields.CharField(max_length=1026)
    # platform_version = modellib.DeferredForeignKey('PlatformVersion') # possible fk
    product_version = fields.CharField(max_length=1026) # possible fk
    platform_name = fields.CharField(max_length=1026)
    platform_usage_terms = fields.CharField(max_length=1026)
    mode = fields.CharField(max_length=1026)
    enabled = fields.BooleanField(max_length=1026)
    configurable = fields.BooleanField()
    abstract = fields.BooleanField()
    mirror_permission = fields.BooleanField()
    # repository_url = modellib.HrefField() # no clue
    # content_sources = models.ManyToManyField('ContentSources', through='Source', db_column='content_source_id') # not sure
    content_sources = models.ForeignKey('ContentSources', db_column='content_source_id')
    platform_type = fields.CharField(max_length=1026)
    platform_status = models.ForeignKey('PlatformSourceStatus') # not sure this is the correct model to point to
    content_source_types = models.ForeignKey('SourceType', db_column='content_source_type')
    load = models.ForeignKey('PlatformLoad')
    # image_type_definitions = modellib.ForeignKey('ImageTypeDefinition') # model doesn't exist yet
    is_platform = fields.BooleanField()
    platform_versions = modellib.DeferredManyToManyField('PlatformVersion', db_column='plaform_id')


class Status(AbstractStatus):
    _xobj = xobj.XObjMetadata(tag='status')
    

class SourceStatus(AbstractStatus):
    class Meta:
        verbose_name = 'content_source_status'
    
    source_type = modellib.ForeignKey('SourceType')
    short_name = fields.CharField(max_length=1026, unique=True)
    
    _xobj = xobj.XObjMetadata(tag='source_status')
    
    
class PlatformSourceStatus(AbstractStatus):
    class Meta:
        verbose_name = 'platform_source_status'
    
    _xobj = xobj.XObjMetadata(tag='platform_source_status')
    

class Sources(modellib.Collection):
    class Meta:
        abstract = True
    list_fields = ['source']

    _xobj = xobj.XObjMetadata(tag='sources')
    
    
class Source(modellib.XObjIdModel):
    class Meta:
        verbose_name = 'content_source'
    
    content_source_id = models.AutoField(primary_key=True) # believe should be AutoField/IntegerField
    name = fields.CharField(max_length=1026)
    short_name = fields.CharField(max_length=1026, unique=True)
    default_source = fields.BooleanField()
    order_index = fields.IntegerField()
    content_source_type = models.ForeignKey('SourceType') # possible fk
    enabled = fields.BooleanField()
    content_source_status = models.ForeignKey('SourceStatus')
    # resource_errors = models.ForeignKey('SourceError') # I think this points to SourceError
    
    _xobj = xobj.XObjMetadata(tag='source')

    
class NuSource(AbstractSource):
    class Meta:
        verbose_name = 'content_source'
    user_name = fields.CharField(max_length=1026)
    passwd = fields.CharField(max_length=1026)

    _xobj = xobj.XObjMetadata(tag='nu_source')

    
class SmtSource(AbstractSource):
    class Meta:
        verbose_name = 'content_source'
        
    user_name = fields.CharField(max_length=1026)
    passwd = fields.CharField(max_length=1026)
    source_url = fields.CharField(max_length=1026)
    
    _xobj = xobj.XObjMetadata(tag='smt_source')
    
    
class RhnSource(AbstractSource):
    class Meta:
        verbose_name = 'content_source'
        
    user_name = fields.CharField(max_length=1026)
    passwd = fields.CharField(max_length=1026)
    
    _xobj = xobj.XObjMetadata(tag='rhn_source')
    
    
class SatelliteSource(AbstractSource):
    class Meta:
        verbose_name = 'content_source'
        
    user_name = fields.CharField(max_length=1026)
    passwd = fields.CharField(max_length=1026)
    source_url = fields.CharField(max_length=1026)
    
    _xobj = xobj.XObjMetadata(tag='satellite_source')


class SourceTypes(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['source_type']
    _xobj = xobj.XObjMetadata(tag='source_types')
    
    
class SourceType(modellib.XObjIdModel):
    class Meta:
        verbose_name = 'content_source_type'
    
    content_source_type = fields.CharField(max_length=1026)
    required = fields.BooleanField()
    singleton = fields.BooleanField()
    # instances = models.ManyToManyField('ContentSourceInstances', through='Source', db_column='content_source_id') # not sure if is correct model to point to, also is this really m2m?
    instances = models.ForeignKey('SourceInstances', db_column='content_source_id')
    # config_descriptor = fields.UrlField() # think this points to other restlib model
    # status_test = fields.UrlField() # what the hell is this?
    
    _xobj = xobj.XObjMetadata(tag='source_type')


class SourceTypeDescriptor(modellib.XObjIdModel):
    pass
    
    
class ContentSourceInstances(modellib.Collection):
    class Meta:
        verbose_name = 'content_sources'
    list_fields = ['source']
    _xobj = xobj.XObjMetadata(tag='content_source_instances')


class ContentSources(modellib.Collection):
    list_fields = ['source_type']
    _xobj = xobj.XObjMetadata(tag='content_sources')
    
    
class SourceInstances(modellib.Collection):
    class Meta:
        verbose_name = 'instances'
    list_fields = ['source']
    _xobj = xobj.XObjMetadata(tag='source_instances')


class PlatformVersions(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform_version']
    _xobj = xobj.XObjMetadata(tag='platform_versions')


class PlatformVersion(modellib.XObjIdModel):
    class Meta:
        verbose_name = 'platform_version'
    name = fields.CharField(max_length=1026)
    version = fields.CharField(max_length=1026)
    revision = fields.CharField(max_length=1026)
    label = fields.CharField(max_length=1026)
    ordering = fields.CharField(max_length=1026)
    platform_id = models.ForeignKey('Platform', db_column='platform_id') # possible fk field
    _xobj = xobj.XObjMetadata(tag='platform_version')
    

class EmptyPlatformVersions(modellib.Collection):
    class Meta:
        verbose_name = 'platform_version'
    _xobj = xobj.XObjMetadata(tag='EmptyPlatformVersions')


class Platforms(modellib.Collection):
    list_fields = ['platform']
    _xobj = xobj.XObjMetadata(tag='platforms')


class Platform(AbstractPlatform):
    _xobj = xobj.XObjMetadata(tag='platform')
      
      
class ProductPlatform(AbstractPlatform):
    class Meta(object):
        verbose_name = 'platform'

    host_name = fields.CharField(max_length=1026)
    _xobj = xobj.XObjMetadata(tag='product_platform')
    
    
class PlatformContentErrors(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform_content_error']
    _xobj = xobj.XObjMetadata(tag='platform_content_errors')
    
    
class PlatformContentError(modellib.XObjModel):
    source_type = modellib.ForeignKey('SourceType')
    short_name = fields.CharField(max_length=1026)
    error_id = fields.IntegerField()
    
    _xobj = xobj.XObjMetadata(tag='platform_content_error')
    
    
class PlatformLoadStatusStub(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(tag='platform_load_status_stub')
    
    
class PlatformLoad(modellib.XObjIdModel):
    load_uri = fields.CharField(max_length=1026)
    job_id = fields.CharField(max_length=1026)
    platform_id = models.ForeignKey('Platform', db_column='platform_id')
    # job = fields.UrlField()
    
    _xobj = xobj.XObjMetadata(tag='platform_load')
    
    
class PlatformLoadStatus(modellib.XObjModel):
    code = fields.IntegerField()
    message = fields.CharField(max_length=1026)
    is_final = fields.BooleanField()

    _xobj = xobj.XObjMetadata(tag='platform_load_status')
    

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
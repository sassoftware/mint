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


# class AbstractSource(modellib.XObjIdModel):
#     class Meta:
#         abstract = True
#     
#     content_source_id = models.AutoField(primary_key=True) # used to be charfield in old code
#     name = fields.CharField(max_length=1026) # is this unique
#     short_name = fields.CharField(max_length=1026, unique=True)
#     default_source = fields.BooleanField()
#     order_index = fields.IntegerField()
#     content_source_type = models.CharField(max_length=1026)
#     enabled = fields.BooleanField()
#     content_source_status = models.ForeignKey('SourceStatus', null=True)
#     # resource_errors = fields.UrlField() # what the heck does this go to
#     
#     def serialize(self, request=None):
#         xobj_model = modellib.XObjIdModel.serialize(self, request)
#         content_source_type = SourceType.objects.get(content_source_type=self.content_source_type)
#         serialized_content_source_type = content_source_type.serialize(request)
#         xobj_model.content_source_type = serialized_content_source_type
#         return xobj_model
#         
# 
# class AbstractStatus(modellib.XObjIdModel):
#     class Meta:
#         abstract = True
# 
#     connected = fields.BooleanField()
#     valid = fields.BooleanField()
#     message = models.TextField()
# 
# 
# class AbstractPlatform(modellib.XObjIdModel):
#     class Meta:
#         abstract = True
#     
#     platform_id = models.AutoField(primary_key=True)
#     platform_trove_name = fields.CharField(max_length=1026)
#     repository_host_name = fields.CharField(max_length=1026)
#     label = fields.CharField(max_length=1026)
#     # product_version = fields.CharField(max_length=1026) # not sure if needed or not
#     platform_name = fields.CharField(max_length=1026)
#     platform_usage_terms = fields.CharField(max_length=1026)
#     mode = fields.CharField(max_length=1026)
#     enabled = fields.BooleanField(max_length=1026)
#     configurable = fields.BooleanField()
#     abstract = fields.BooleanField()
#     mirror_permission = fields.BooleanField()
#     # repository_url = modellib.HrefField() # no clue
#     content_sources = models.ManyToManyField('ContentSources', through='Source', db_column='content_source_id')
#     platform_type = fields.CharField(max_length=1026)
#     platform_status = models.ForeignKey('PlatformSourceStatus') # not sure this is the correct model to point to
#     content_source_types = models.ForeignKey('SourceType', db_column='content_source_type')
#     load = models.ForeignKey('PlatformLoad')
#     # image_type_definitions = modellib.ForeignKey('ImageTypeDefinition') # model doesn't exist yet
#     is_platform = fields.BooleanField()
#     # both of platform_version and platform_versions are in original model for platform as URLFields,
#     # not sure if both are necessary and what the URLFields translate to
#     platform_version = modellib.DeferredForeignKey('PlatformVersion') # possible fk
#     platform_versions = modellib.DeferredManyToManyField('PlatformVersion', db_column='plaform_id')
#     project = models.ForeignKey('rbuilder.projects.project')
# 
#     def serialize(self, request=None):
#         xobj_model = modellib.XObjIdModel.serialize(self, request)
#         # xobj_model.repository_url = self.project.getRepositoryUrl()
#         return xobj_model
# 
# class PlatformSource(modellib.XObjIdModel):
#     platform = models.ForeignKey('Platform')
#     platform_id = models.ForeignKey()
# 
# 
# class Status(AbstractStatus):
#     _xobj = xobj.XObjMetadata(tag='status')
#     
# 
# class SourceStatus(AbstractStatus):
#     class Meta:
#         verbose_name = 'content_source_status'
#     
#     content_source_type = modellib.ForeignKey('SourceType', db_column='content_source_type')
#     short_name = fields.CharField(max_length=1026, unique=True)
#     
#     _xobj = xobj.XObjMetadata(tag='source_status')
#     
#     
# class PlatformSourceStatus(AbstractStatus):
#     class Meta:
#         verbose_name = 'platform_source_status'
#     
#     _xobj = xobj.XObjMetadata(tag='platform_source_status')
#     
# 
# class Sources(modellib.Collection):
#     class Meta:
#         abstract = True
#     list_fields = ['source']
# 
#     _xobj = xobj.XObjMetadata(tag='sources')
#     
#     
# class Source(modellib.XObjIdModel):
#     class Meta:
#         verbose_name = 'content_source'
#     
#     content_source_id = models.AutoField(primary_key=True) # used to be Charfield in old code
#     name = fields.CharField(max_length=1026)
#     short_name = fields.CharField(max_length=1026, unique=True)
#     default_source = fields.BooleanField()
#     order_index = fields.IntegerField()
#     content_source_type = models.ForeignKey('SourceType', db_column='content_source_type')
#     enabled = fields.BooleanField()
#     content_source_status = models.ForeignKey('SourceStatus')
#     # resource_errors = models.ForeignKey('SourceError') # I think this points to SourceError but not sure
#     
#     _xobj = xobj.XObjMetadata(tag='source')
# 
#     
# class NuSource(AbstractSource):
#     class Meta:
#         verbose_name = 'content_source'
#     user_name = fields.CharField(max_length=1026)
#     passwd = fields.CharField(max_length=1026)
# 
#     _xobj = xobj.XObjMetadata(tag='nu_source')
# 
#     
# class SmtSource(AbstractSource):
#     class Meta:
#         verbose_name = 'content_source'
#         
#     user_name = fields.CharField(max_length=1026)
#     passwd = fields.CharField(max_length=1026)
#     source_url = fields.CharField(max_length=1026)
#     
#     _xobj = xobj.XObjMetadata(tag='smt_source')
#     
#     
# class RhnSource(AbstractSource):
#     class Meta:
#         verbose_name = 'content_source'
#         
#     user_name = fields.CharField(max_length=1026)
#     passwd = fields.CharField(max_length=1026)
#     
#     _xobj = xobj.XObjMetadata(tag='rhn_source')
#     
#     
# class SatelliteSource(AbstractSource):
#     class Meta:
#         verbose_name = 'content_source'
#         
#     user_name = fields.CharField(max_length=1026)
#     passwd = fields.CharField(max_length=1026)
#     source_url = fields.CharField(max_length=1026)
#     
#     _xobj = xobj.XObjMetadata(tag='satellite_source')
# 
# 
# class SourceTypes(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['source_type']
#     _xobj = xobj.XObjMetadata(tag='source_types')
#     
#     
# class SourceType(modellib.XObjIdModel):
#     class Meta:
#         verbose_name = 'content_source_type'
#     
#     content_source_type = fields.CharField(max_length=1026)
#     required = fields.BooleanField()
#     singleton = fields.BooleanField()
#     # config_descriptor = fields.UrlField() # think this points to other restlib model
#     # status_test = fields.UrlField() # what the hell is this?
#     
#     _xobj = xobj.XObjMetadata(tag='source_type')
# 
# 
# class SourceTypeDescriptor(modellib.XObjIdModel):
#     pass
#     
#     
# class ContentSourceInstances(modellib.Collection):
#     class Meta:
#         verbose_name = 'content_sources'
#     list_fields = ['source']
#     _xobj = xobj.XObjMetadata(tag='content_source_instances')
# 
# 
# class ContentSources(modellib.Collection):
#     list_fields = ['source_type']
#     _xobj = xobj.XObjMetadata(tag='content_sources')
#     
#     
# class SourceInstances(modellib.Collection):
#     class Meta:
#         verbose_name = 'instances'
#     list_fields = ['source']
#     _xobj = xobj.XObjMetadata(tag='source_instances')
# 
# 
# class PlatformVersions(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['platform_version']
#     _xobj = xobj.XObjMetadata(tag='platform_versions')
# 
# 
# class PlatformVersion(modellib.XObjIdModel):
#     class Meta:
#         verbose_name = 'platform_version'
#     name = fields.CharField(max_length=1026)
#     version = fields.CharField(max_length=1026)
#     revision = fields.CharField(max_length=1026)
#     label = fields.CharField(max_length=1026)
#     ordering = fields.CharField(max_length=1026)
#     platform_id = models.ForeignKey('Platform', db_column='platform_id')
#     _xobj = xobj.XObjMetadata(tag='platform_version')
#     
# 
# class EmptyPlatformVersions(modellib.Collection):
#     class Meta:
#         verbose_name = 'platform_version'
#     _xobj = xobj.XObjMetadata(tag='EmptyPlatformVersions')
# 
# 
# class Platforms(modellib.Collection):
#     list_fields = ['platform']
#     _xobj = xobj.XObjMetadata(tag='platforms')
# 
# 
# class Platform(AbstractPlatform):
#     _xobj = xobj.XObjMetadata(tag='platform')
#       
#       
# class ProductPlatform(AbstractPlatform):
#     class Meta(object):
#         verbose_name = 'platform'
# 
#     host_name = fields.CharField(max_length=1026)
#     _xobj = xobj.XObjMetadata(tag='product_platform')
#     
#     
# class PlatformContentErrors(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['platform_content_error']
#     _xobj = xobj.XObjMetadata(tag='platform_content_errors')
#     
#     
# class PlatformContentError(modellib.XObjModel):
#     content_source_type = modellib.ForeignKey('SourceType')
#     short_name = fields.CharField(max_length=1026)
#     error_id = fields.IntegerField()
#     
#     _xobj = xobj.XObjMetadata(tag='platform_content_error')
#     
#     
# class PlatformLoadStatusStub(modellib.XObjModel):
#     _xobj = xobj.XObjMetadata(tag='platform_load_status_stub')
#     
#     
# class PlatformLoad(modellib.XObjIdModel):
#     load_uri = fields.CharField(max_length=1026)
#     job_id = fields.CharField(max_length=1026)
#     platform_id = models.ForeignKey('Platform', db_column='platform_id')
#     # job = fields.UrlField() # fk to jobs instance?
#     
#     _xobj = xobj.XObjMetadata(tag='platform_load')
#     
#     
# class PlatformLoadStatus(modellib.XObjModel):
#     code = fields.IntegerField()
#     message = fields.CharField(max_length=1026)
#     is_final = fields.BooleanField()
# 
#     _xobj = xobj.XObjMetadata(tag='platform_load_status')



class AbstractPlatform(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    platform_id = models.AutoField(primary_key=True)
    platform_trove_name = fields.CharField(max_length=1026)
    repository_host_name = fields.CharField(max_length=1026)
    label = fields.CharField(max_length=1026)
    product_version = fields.CharField(max_length=1026)
    platform_name = fields.CharField(max_length=1026)
    platform_usage_terms = fields.CharField(max_length=1026)
    mode = fields.CharField(max_length=1026)
    enabled = fields.BooleanField(max_length=1026)
    configurable = fields.BooleanField()
    abstract = fields.BooleanField()
    mirror_permission = fields.BooleanField()
    # repository_url = modellib.HrefField() # no clue
    content_sources = models.ManyToManyField('ContentSources', through='Source', db_column='content_source_id')
    platform_type = fields.CharField(max_length=1026)
    platform_status = models.ForeignKey('PlatformSourceStatus') # not sure this is the correct model to point to
    content_source_types = models.ForeignKey('SourceType', db_column='content_source_type')
    load = models.ForeignKey('PlatformLoad')
    # image_type_definitions = modellib.ForeignKey('ImageTypeDefinition') # model doesn't exist yet
    is_platform = fields.BooleanField()
    # both of platform_version and platform_versions are in original model for platform as URLFields,
    # not sure if both are necessary and what the URLFields translate to
    # platform_version = modellib.DeferredForeignKey('PlatformVersion')
    platform_versions = modellib.DeferredManyToManyField('PlatformVersion', db_column='plaform_id')
    project = models.ForeignKey('rbuilder.projects.project')

    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        # xobj_model.repository_url = self.project.getRepositoryUrl()
        return xobj_model


class Platforms(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform']


class Platform(AbstractPlatform):
    class Meta:
        abstract = False


class ProductPlatforms(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['product_platform']


class ProductPlatform(AbstractPlatform):
    class Meta:
        abstract = False
        
    hostname = fields.CharField(max_length=1026)


class PlatformSources(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['platform_source']
    
    
class PlatformSource(modellib.XObjIdModel):
    platform = models.ForeignKey('Platform')
    platform_id = models.ForeignKey('Platform', db_column='platform_id')
    

class PlatformVersions(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['platform_version']
    
    
class PlatformVersion(modellib.XObjIdModel):
    name = fields.CharField(max_length=1026)
    version = fields.CharField(max_length=1026)
    revision = fields.CharField(max_length=1026)
    label = fields.CharField(max_length=1026)
    ordering = fields.CharField(max_length=1026)
    platform_id = models.ForeignKey('Platform', db_column='platform_id')


class PlatformLoads(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['platform_load']
    
    
class PlatformLoad(modellib.XObjIdModel):
    load_uri = fields.CharField()
    job_id = fields.CharField()
    platform_id = fields.IntegerField()
    # job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
    platform_load_status = models.ForeignKey('PlatformLoadStatus')


class PlatformBuildTemplates(modellib.Collection):
    class Meta:
        abstract = True
    
    
class PlatformBuildTemplate(modellib.XObjIdModel):
    pass
    

class Sources(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['source']
    
    
class AbstractSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    content_source_id = models.AutoField(primary_key=True)
    name = fields.CharField(max_length=1026)
    short_name = fields.CharField(max_length=1026, unique=True)
    default_source = fields.BooleanField()
    order_index = fields.IntegerField()
    content_source_type = models.CharField(max_length=1026)
    enabled = fields.BooleanField()
    content_source_status = models.ForeignKey('SourceStatus', null=True)
    # resource_errors = fields.UrlField() # what the heck does this go to
    
    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        content_source_type = SourceType.objects.get(content_source_type=self.content_source_type)
        serialized_content_source_type = content_source_type.serialize(request)
        xobj_model.content_source_type = serialized_content_source_type
        return xobj_model


class Source(AbstractSource):
    class Meta:
        abstract = False
    

class NuSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    

class SmtSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    source_url = fields.CharField(max_length=1026)
    
    
class RhnSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    
    
class SatelliteSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    source_url = fields.CharField(max_length=1026)
    

class SourceTypes(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['source_type']
    
    
class SourceType(modellib.XObjIdModel):
    content_source_type = fields.CharField(max_length=1026)
    required = fields.BooleanField()
    singleton = fields.BooleanField()
    # config_descriptor = fields.UrlField() # think this points to other restlib model
    # status_test = fields.UrlField() # what the hell is this?


class ContentSources(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['source_type']


class AbstractStatus(modellib.XObjIdModel):
    class Meta:
        abstract = True

    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = models.TextField()


class Statuses(modellib.Collection):
    class Meta:
        abstract = True
    
    
class Status(AbstractStatus):
    class Meta:
        abstract = False
    

class PlatformLoadStatuses(Statuses):
    class Meta:
        abstract = True
    
    
class PlatformLoadStatus(modellib.XObjIdModel):
    code = fields.IntegerField()
    message = fields.CharField(max_length=1026)
    is_final = fields.BooleanField()
    

class SourceStatus(AbstractStatus):
    class Meta:
        abstract = False
    
    content_source_type = modellib.ForeignKey('SourceType', db_column='content_source_type')
    short_name = fields.CharField(max_length=1026, unique=True)


class PlatformContentErrors(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['platform_content_error']


class PlatformContentError(modellib.XObjModel):
    content_source_type = modellib.ForeignKey('SourceType')
    short_name = fields.CharField(max_length=1026)
    error_id = fields.IntegerField()



for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
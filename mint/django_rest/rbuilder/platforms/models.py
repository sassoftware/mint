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
from mint.django_rest.rbuilder.projects import models as projectsmodels


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
    # content_sources = models.ManyToManyField('ContentSource', through='PlatformContentSource')
    platform_type = fields.CharField(max_length=1026)
    platform_status = models.ForeignKey('SourceStatus') # not sure this is the correct model to point to
    content_source_types = models.ForeignKey('ContentSourceType')
    load = models.ForeignKey('PlatformLoad')
    # image_type_definitions = modellib.ForeignKey('ImageTypeDefinition') # model doesn't exist yet
    is_platform = fields.BooleanField()
    # both of platform_version and platform_versions are in original model for platform as URLFields,
    # not sure if both are necessary and what the URLFields translate to
    # platform_version = modellib.DeferredForeignKey('PlatformVersion')
    # platform_versions = modellib.DeferredManyToManyField('PlatformVersion')
    platform_versions = modellib.DeferredForeignKey('PlatformVersion')
    project = models.ForeignKey(projectsmodels.Project)

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
    content_sources = models.ManyToManyField('ContentSource', through='PlatformContentSource')

class ProductPlatforms(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['product_platform']

class ProductPlatform(AbstractPlatform):
    class Meta:
        abstract = False
        
    hostname = fields.CharField(max_length=1026)
    content_sources = models.ManyToManyField('ContentSource', through='ProductPlatformContentSource')


class ProductPlatformContentSource(modellib.XObjIdModel):
    class Meta:
        abstract = False
        
    content_source = models.ForeignKey('ContentSource')
    product_platform = models.ForeignKey('ProductPlatform')


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
    load_uri = fields.CharField(max_length=1026)
    job_id = fields.CharField(max_length=1026)
    platform_id = fields.IntegerField()
    # job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
    platform_load_status = models.ForeignKey('PlatformLoadStatus', db_column='platform_load_status_id')


class PlatformBuildTemplates(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform_build_template']
    
    
class PlatformBuildTemplate(modellib.XObjIdModel):
    class Meta:
        abstract = False
    

class Sources(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['content_source']
    
    
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
    # content_source_status = models.ForeignKey('SourceStatus', null=True)
    # resource_errors = fields.UrlField() # what the heck does this go to
    
    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        content_source_type = ContentSourceType.objects.get(content_source_type=self.content_source_type)
        serialized_content_source_type = content_source_type.serialize(request)
        xobj_model.content_source_type = serialized_content_source_type
        return xobj_model


class PlatformContentSource(modellib.XObjIdModel):
    platform = models.ForeignKey('Platform')
    content_source = models.ForeignKey('ContentSource')
   

class NuSource(AbstractSource):
    class Meta:
        abstract = True
    
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    

class SmtSource(AbstractSource):
    class Meta:
        abstract = True
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    source_url = fields.CharField(max_length=1026)
    
    
class RhnSource(AbstractSource):
    class Meta:
        abstract = True
    
    user_name = fields.CharField(max_length=1026)
    password = fields.ProtectedField()
    
    
class SatelliteSource(AbstractSource):
    class Meta:
        abstract = True
        
    source_url = fields.CharField(max_length=1026)
    

class ContentSourceTypes(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['content_source_type']
    
    
class ContentSourceType(modellib.XObjIdModel):
    content_source_type = fields.CharField(max_length=1026)
    required = fields.BooleanField()
    singleton = fields.BooleanField()
    # config_descriptor = fields.UrlField() # think this points to other restlib model
    # status_test = fields.UrlField() # what the hell is this?


class ContentSources(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['content_source_type']


class ContentSource(AbstractSource):
    class Meta:
        abstract = False


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
    platform_load_status_id = models.AutoField(primary_key=True)
    code = fields.IntegerField()
    message = fields.CharField(max_length=1026)
    is_final = fields.BooleanField()
    

class SourceStatus(AbstractStatus):
    class Meta:
        abstract = False
    
    content_source_type = modellib.ForeignKey('ContentSourceType')
    short_name = fields.CharField(max_length=1026, unique=True)


class PlatformContentErrors(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['platform_content_error']


class PlatformContentError(modellib.XObjModel):
    content_source_type = modellib.ForeignKey('ContentSourceType')
    short_name = fields.CharField(max_length=1026)
    error_id = fields.IntegerField()



for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

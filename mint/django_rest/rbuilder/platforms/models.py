#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.rbuilder.platforms import fields
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.modellib import basemodels # hack, because of modellib in Platform
import sys
from xobj import xobj


class Platforms(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform']


class Platform(modellib.XObjIdModel):
    class Meta:
        db_table = 'Platforms'
    
    _MODE_CHOICES = (('manual', 'manual'), ('auto', 'auto'))
    
    platform_id = models.AutoField(primary_key=True, db_column='platformId')
    label = models.CharField(max_length=1026, unique=True)
    mode = models.CharField(max_length=1026, default='manual', choices=_MODE_CHOICES)
    enabled = models.IntegerField(default=1)
    projects = modellib.DeferredForeignKey('projects.Project', db_column='projectId')
    platform_name = models.CharField(max_length=1026, db_column='platformName')
    configurable = models.BooleanField(default=False)
    abstract = models.BooleanField(default=False)
    is_from_disk = models.BooleanField(default=False, db_column='isFromDisk')
    time_refresed = basemodels.DateTimeUtcField() # hack, modellib keeps evaluating to None
    
    # SyntheticFields -- fields with no column in the db
    # most of these are deferred fk's or CharFields in the old code
    platform_trove_name = modellib.SyntheticField() # charfield
    repository_host_name = modellib.SyntheticField() # charfield
    repository_url = modellib.SyntheticField() # genuine synthetic field
    product_version = modellib.SyntheticField() # fk
    platform_usage_terms = modellib.SyntheticField() # charfield
    mirror_permission = modellib.SyntheticField() # boolean
    platform_type = modellib.SyntheticField() # charfield
    load = modellib.SyntheticField() # fk
    image_type_definitions = modellib.SyntheticField() # fk
    content_sources = modellib.SyntheticField() # fk
    content_source_types = modellib.SyntheticField() # fk
    platform_status = modellib.SyntheticField() # fk
    
    
class ContentSources(modellib.Collection):
    """
    Container for model that used to be called PlatformSource
    """
    class Meta:
        abstract = True
    list_fields = ['content_source']
    
    
class ContentSource(modellib.XObjIdModel):
    """
    Called PlatformSource in the db
    """
    class Meta:
        db_table = 'PlatformSources'
        
    content_source_id = models.AutoField(primary_key=True, db_column='platformSourceId')
    name = models.CharField(max_length=1026)
    default_source = models.IntegerField(db_column='defaultSource', default=0)
    short_name = models.CharField(max_length=1026, unique=True, db_column='shortName')
    content_source_type = models.CharField(max_length=1026, db_column='contentSourceType')
    order_index = models.IntegerField(db_column='orderIndex')
    
    # fields on the old model w/o corresponding column in the db
    enabled = modellib.SyntheticField() # booleanfield
    content_source_status = modellib.SyntheticField() # fk
    resource_errors = modellib.SyntheticField() # fk
    source_url = modellib.SyntheticField() # charfield/textfield


class ContentSourceTypes(modellib.Collection):
    """
    Container for what is called PlatformsContentSourceTypes in the db
    """
    class Meta:
        abstract = True
    
    list_fields = ['content_source_type']
    

class ContentSourceType(modellib.XObjIdModel):
    """
    Is PlatformsContentSourceTypes in the db
    """
    class Meta:
        db_table = 'PlatformsContentSourceTypes'
        
    platform_id = modellib.DeferredForeignKey('Platform')
    content_source_type = models.CharField(max_length=1026, db_column='contentSourceType')
    
    # Fields w/o a corresponding db column
    required = modellib.SyntheticField() # booleanfield
    singleton = modellib.SyntheticField() # booleanfield
    instances = modellib.SyntheticField() # fk
    config_descriptor = modellib.SyntheticField() # fk
    status_test = modellib.SyntheticField() # fk
    

class PlatformsPlatformSources(modellib.XObjModel):
    platform_id = modellib.DeferredForeignKey('Platform')
    platform_source_id = modellib.ForeignKey('ContentSource')


class PlatformVersions(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['platform_version']


class PlatformVersion(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    name = models.CharField(max_length=1026)
    version = models.CharField(max_length=1026)
    revision = models.CharField(max_length=1026)
    label = models.CharField(max_length=1026)
    ordering = models.DecimalField()


class PlatformLoads(modellib.Collection):
    class Meta:
        abstract = True
    list_fields = ['platform_load']


class PlatformLoad(modellib.XObjIdModel):
    class Meta:
        abstract = True
    load_uri = models.CharField(max_length=1026)
    job_id = models.IntegerField()
    platform_id = models.IntegerField()
    # job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
    platform_load_status = models.ForeignKey('PlatformLoadStatus')


class PlatformLoadStatus(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    code = models.IntegerField()
    message = models.CharField(max_length=1026)
    is_final = models.BooleanField()


### OLD ###
# class Platforms(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['platform']
# 
# 
# class Platform(modellib.XObjIdModel):
#     class Meta:
#         db_table = 'Platforms'
#     
#     _MODE_CHOICES = (('manual', 'manual'), ('auto', 'auto'))
#     
#     platform_id = models.AutoField(primary_key=True, db_column='platformid')
#     platform_trove_name = modellib.SyntheticField() # used to be a CharField
#     label = models.CharField(max_length=1026, unique=True)
#     mode = models.CharField(max_length=1026, default='manual', choices=_MODE_CHOICES)
#     enabled = models.IntegerField(default=1)
#     projects = modellib.DeferredForeignKey('projects.Project')
#     platform_name = models.CharField(max_length=1026, db_column='platformName')
#     configurable = models.BooleanField(default=False)
#     abstract = models.BooleanField(default=False)
#     is_from_disk = models.BooleanField(default=False, db_column='isFromDisk')
#     time_refresed = basemodels.DateTimeUtcField() # hack, modellib keeps evaluating to None
#     repository_host_name = models.CharField(max_length=1026)
#     product_version = models.CharField(max_length=1026)
#     platform_usage_terms = models.CharField(max_length=1026)
# 
# 
# class ProductPlatforms(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['product_platform']
# 
# class ProductPlatform(modellib.XObjIdModel):
#     class Meta:
#         abstract = False
#     platform_id = models.AutoField(primary_key=True, db_column='platformid')
#     label = models.CharField(max_length=1026)
#     mode = models.CharField(max_length=1026)
#     enabled = models.IntegerField()
#     projects = modellib.DeferredForeignKey('projects.Project')
#     platform_name = models.CharField(max_length=1026, db_column='platformName')
#     configurable = models.BooleanField(default=False)
#     abstract = models.BooleanField(default=False)
#     is_from_disk = models.BooleanField(default=False, db_column='isFromDisk')
#     time_refresed = basemodels.DateTimeUtcField() # hack, modellib keeps evaluating to None
#     hostname = fields.CharField(max_length=1026)
#     content_sources = models.ManyToManyField('ContentSource', through='ProductPlatformContentSource')
# 
# 
# class ProductPlatformContentSource(modellib.XObjIdModel):
#     class Meta:
#         abstract = False
#         
#     content_source = models.ForeignKey('ContentSource')
#     product_platform = models.ForeignKey('ProductPlatform')
# 
# 
# class PlatformVersions(modellib.Collection):
#     class Meta:
#         abstract = True
#     
#     list_fields = ['platform_version']
#     
#     
# class PlatformVersion(modellib.XObjIdModel):
#     name = fields.CharField(max_length=1026)
#     version = fields.CharField(max_length=1026)
#     revision = fields.CharField(max_length=1026)
#     label = fields.CharField(max_length=1026)
#     ordering = fields.CharField(max_length=1026)
# 
# 
# 
# class PlatformLoads(modellib.Collection):
#     class Meta:
#         abstract = True
#     
#     list_fields = ['platform_load']
#     
#     
# class PlatformLoad(modellib.XObjIdModel):
#     load_uri = fields.CharField(max_length=1026)
#     job_id = fields.IntegerField()
#     platform_id = fields.IntegerField()
#     # job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
#     platform_load_status = models.ForeignKey('PlatformLoadStatus')
# 
# 
# class PlatformBuildTemplates(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['platform_build_template']
#     
#     
# class PlatformBuildTemplate(modellib.XObjIdModel):
#     class Meta:
#         abstract = False
#     
# 
# class Sources(modellib.Collection):
#     class Meta:
#         abstract = True
#         
#     list_fields = ['content_source']
# 
# 
# class AbstractSource(modellib.XObjIdModel):
#     class Meta:
#         abstract = True
#     content_source_id = models.AutoField(primary_key=True, db_column='platformSourceId')
#     name = models.CharField(max_length=1026)
#     short_name = models.CharField(max_length=1026, unique=True, db_column='shortName')
#     default_source = models.IntegerField()
#     order_index = models.IntegerField()
#     content_source_type = models.CharField(max_length=1026, db_column='contentSourceType')
#     enabled = fields.BooleanField()
# 
# 
# class PlatformContentSource(modellib.XObjIdModel):
#     platform = models.ForeignKey('Platform')
#     content_source = models.ForeignKey('ContentSource')
#    
# 
# class NuSource(AbstractSource):
#     class Meta:
#         abstract = True
#     
#     user_name = fields.CharField(max_length=1026)
#     password = fields.ProtectedField()
#     
# 
# class SmtSource(AbstractSource):
#     class Meta:
#         abstract = True
#     user_name = fields.CharField(max_length=1026)
#     password = fields.ProtectedField()
#     source_url = fields.CharField(max_length=1026)
#     
#     
# class RhnSource(AbstractSource):
#     class Meta:
#         abstract = True
#     
#     user_name = fields.CharField(max_length=1026)
#     password = fields.ProtectedField()
#     
#     
# class SatelliteSource(AbstractSource):
#     class Meta:
#         abstract = True
#         
#     source_url = fields.CharField(max_length=1026)
#     
# 
# class ContentSourceTypes(modellib.Collection):
#     class Meta:
#         abstract = True
#     
#     list_fields = ['content_source_type']
#     
#     
# class ContentSourceType(modellib.XObjIdModel):
#     class Meta:
#         db_table = 'PlatformsContentSourceTypes'
#         
#     content_source_type = fields.CharField(max_length=1026)
#     required = fields.BooleanField()
#     singleton = fields.BooleanField()
# 
#     _xobj_hidden_accessors = set(['platform_set', 'sourcestatus_set', 'productplatform_set',
#                                  'platformcontenterror_set'])
# 
# class ContentSources(modellib.Collection):
#     class Meta:
#         abstract = True
#     
#     list_fields = ['content_source_type']
# 
# 
# class ContentSource(AbstractSource):
#     class Meta:
#         abstract = False
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
# class Statuses(modellib.Collection):
#     class Meta:
#         abstract = True
#     
#     
# class Status(AbstractStatus):
#     class Meta:
#         abstract = False
#     
# 
# class PlatformLoadStatuses(Statuses):
#     class Meta:
#         abstract = True
#     
#     list_fields = ['platform_load_status']
#     
#     
# class PlatformLoadStatus(modellib.XObjIdModel):
#     platform_load_status_id = models.AutoField(primary_key=True)
#     code = fields.IntegerField()
#     message = fields.CharField(max_length=1026)
#     is_final = fields.BooleanField()
#     
# 
# class SourceStatus(AbstractStatus):
#     class Meta:
#         abstract = False
#     
#     content_source_status_id = models.AutoField(primary_key=True)
#     content_source_type = modellib.ForeignKey('ContentSourceType')
#     short_name = fields.CharField(max_length=1026, unique=True)
# 
# 
# class PlatformContentErrors(modellib.Collection):
#     class Meta:
#         abstract = True
# 
#     list_fields = ['platform_content_error']
# 
# 
# class PlatformContentError(modellib.XObjIdModel):
#     content_source_type = modellib.ForeignKey('ContentSourceType')
#     short_name = fields.CharField(max_length=1026, unique=True)
#     error_id = fields.IntegerField()
# 
# 
# class ImageTypeDefinitions(modellib.XObjIdModel):
#     _xobj = xobj.XObjMetadata(tag='image_type_definitions')
#     
#     image_type_definitions_id = models.AutoField(primary_key=True)
#     
# 
# class ImageDefinitions(modellib.XObjIdModel):
#     _xobj = xobj.XObjMetadata(tag='image_definitions')


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

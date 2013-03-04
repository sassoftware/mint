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
from mint.django_rest.deco import D

## TODO: Change SyntheticFields to correct type (mostly CharFields/BooleanFields/FK's)
##       once the schema is updated (if need be).  Some of the models are listed as
##       abstract as they lack the necessary tables in the db -- and some of the fields on
##       those models are temporarily synthetic because we can't have FK's to abstract models.


class Platforms(modellib.Collection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='platforms')
        
    list_fields = ['platform']


class Platform(modellib.XObjIdModel):
    class Meta:
        db_table = 'platforms'
        ordering = [ 'platform_id' ]

    _xobj = xobj.XObjMetadata(tag='platform')

    _MODE_CHOICES = (('manual', 'manual'), ('auto', 'auto'))

    platform_id = D(models.AutoField(primary_key=True, db_column='platformid'), 'ID of the platform')
    label = D(models.CharField(max_length=1026, unique=True), 'Platform label, must be unique')
    mode = D(models.CharField(max_length=1026, default='manual', choices=_MODE_CHOICES),
        'Charfield, defaults to "manual"')
    enabled = D(models.IntegerField(default=1), 'Is enabled, defaults to integer 1')
    project = D(modellib.DeferredForeignKey('projects.Project', db_column='projectid', null=True),
        'Project attached to the platform, cannot be null')
    platform_name = D(models.CharField(max_length=1026, db_column='platformname'), 'Name of the platform')
    configurable = D(models.BooleanField(default=False), 'Boolean, defaults to False')
    abstract = D(models.BooleanField(default=False), 'Boolean, defaults to False')
    is_from_disk = D(models.BooleanField(default=False, db_column='isfromdisk'), 'Boolean, defaults to False')
    hidden = D(models.BooleanField(default=False), 'Boolean, defaults to False')
    upstream_url = D(models.CharField(), "Upstream repository URL used when creating external project for this platform")
    time_refreshed = D(basemodels.DateTimeUtcField(auto_now_add=True),
        'Time at which the platform was refreshed') # hack, modellib keeps evaluating to None

    # SyntheticFields -- fields with no column in the db
    # most of these are deferred fk's, M2M's, or CharFields in the old code
    platform_trove_name = modellib.SyntheticField() # charfield
    repository_host_name = modellib.SyntheticField() # charfield
    repository_api = modellib.SyntheticField(modellib.HrefField()) # genuine synthetic field
    product_version = modellib.SyntheticField() # fk
    platform_versions = modellib.SyntheticField(modellib.HrefField()) # fk, is this different from product_version ?
    platform_usage_terms = modellib.SyntheticField() # charfield
    mirror_permission = modellib.SyntheticField() # boolean
    platform_type = modellib.SyntheticField() # charfield
    load = modellib.SyntheticField() # fk
    image_type_definitions = modellib.SyntheticField() # fk
    platform_status = modellib.SyntheticField() # fk
    is_platform = modellib.SyntheticField() # booleanfield

    def computeSyntheticFields(self, sender, **kwargs):
        # Platform has yet to be enabled.
        if self.project is None:
            return

        self._computeRepositoryAPI()
        self._computePlatformVersions()

    def _computeRepositoryAPI(self):
        self.repository_api = modellib.HrefField(
            href='/repos/%s/api' % self.project.short_name,
        )

    def _computePlatformVersions(self):
        self.platform_versions = modellib.HrefField(
            href='/api/platforms/%s/platformVersions' % self.platform_id,
        )

class ContentSources(modellib.Collection):
    """
    Container for model that used to be called PlatformSource
    """
    class Meta:
        abstract = True
    
    _xobj = xobj.XObjMetadata(tag='content_sources')
        
    list_fields = ['content_source']
    
    
class ContentSource(modellib.XObjIdModel):
    """
    Called PlatformSource in the db
    """
    class Meta:
        db_table = 'platformsources'
    
    _xobj = xobj.XObjMetadata(tag='content_source')
    
    _xobj_hidden_accessors = set(['content_sources'])
    
    content_source_id = D(models.AutoField(primary_key=True, db_column='platformsourceid'),
        'ID of the content source')
    name = D(models.CharField(max_length=1026), 'Name of the content source')
    default_source = D(models.IntegerField(db_column='defaultsource', default=0),
        'Is integer, defaults to 0')
    short_name = D(modellib.UpdatableKey(models.CharField(max_length=1026, unique=True, db_column='shortname')),
        'Short name of the content source, must be unique')
    content_source_type = D(models.CharField(max_length=1026, db_column='contentsourcetype'),
        'Type of content source')
    order_index = D(models.IntegerField(db_column='orderindex'), 'Integer that defines the order index')
    
    # fields on the old model w/o corresponding column in the db
    enabled = modellib.SyntheticField() # booleanfield/integerfield
    content_source_status = modellib.SyntheticField() # fk
    resource_errors = modellib.SyntheticField() # fk
    source_url = modellib.SyntheticField() # charfield/textfield


class ContentSourceTypes(modellib.Collection):
    """
    Container for what is called PlatformsContentSourceTypes in the db
    """
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='content_source_types')
    list_fields = ['content_source_type']
    

class ContentSourceType(modellib.XObjIdModel):
    """
    Is PlatformsContentSourceTypes in the db
    """
    class Meta:
        db_table = 'platformscontentsourcetypes'
        unique_together = ('platform_id', 'content_source_type')
    
    _xobj = xobj.XObjMetadata(tag='content_source_type')
    
    content_source_type_id = D(models.AutoField(primary_key=True, db_column='contentsourcetypeid'),
        'ID of the source type')
    platform_id = D(modellib.DeferredForeignKey('Platform', db_column='platformid', related_name='content_source_types'),
        'ID to a platform')
    content_source_type = D(models.CharField(max_length=1026, db_column='contentsourcetype'),
        'Actual source type')
    
    # Fields w/o a corresponding db column
    required = modellib.SyntheticField() # booleanfield
    singleton = modellib.SyntheticField() # booleanfield
    instances = modellib.SyntheticField() # fk
    config_descriptor = modellib.SyntheticField() # fk
    status_test = modellib.SyntheticField() # fk
    

class PlatformsPlatformSources(modellib.XObjModel):
    class Meta:
        db_table = 'platformsplatformsources'
    platforms_platform_sources_id = D(models.AutoField(primary_key=True), 'ID of the platform sources')
    platform_id = D(modellib.ForeignKey('Platform', db_column='platformid', related_name='content_sources'),
        'ID of a platform')
    platform_source_id = D(modellib.ForeignKey('ContentSource', db_column='platformsourceid', related_name='content_sources'),
        'ID of a platform source')


class PlatformVersions(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['platform_version']


class PlatformVersion(modellib.XObjIdModel):
    class Meta:
        abstract = True
    
    name = D(models.CharField(max_length=1026), 'Platform version name')
    version = D(models.CharField(max_length=1026), 'Is the platform version')
    revision = D(models.CharField(max_length=1026), 'Is the platform revision')
    label = models.CharField(max_length=1026)
    ordering = D(models.DecimalField(), 'Ordering of the version, is a decimal')


class PlatformLoads(modellib.Collection):
    class Meta:
        abstract = True
    list_fields = ['platform_load']
    _xobj = xobj.XObjMetadata(tag='platform_loads')

class PlatformLoad(modellib.XObjIdModel):
    class Meta:
        abstract = True
    load_uri = D(models.CharField(max_length=1026), 'Uri for the platform load')
    job_id = D(models.IntegerField(), 'ID to a job')
    platform_id = D(models.IntegerField(), 'ID to a platform')
    # job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
    
    # SyntheticFields, fields w/o corresponding column in db
    platform_load_status = modellib.SyntheticField() # fk


class PlatformLoadStatus(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    code = D(models.IntegerField(), 'Integer')
    message = D(models.CharField(max_length=1026), 'Status message')
    is_final = D(models.BooleanField(), 'Is the load status final? Is boolean')


class Status(modellib.XObjIdModel):
    """
    Base class for all statuses except PlatformLoadStatus
    """
    class Meta:
        abstract = True
        
    connected = D(models.BooleanField(), 'Is status connected, boolean')
    valid = D(models.BooleanField(), 'Is status valid? Is boolean')
    message = D(models.CharField(max_length=1026), 'The status message')
    

class NuSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass
    

class SmtSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass


class SatelliteSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass
    

class RhnSource(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass


class PlatformBuildTemplates(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform_build_template']
    
    
class PlatformBuildTemplate(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass


class PlatformContentErrors(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['platform_content_error']


class PlatformContentError(modellib.XObjIdModel):
    class Meta:
        abstract = True
    short_name = D(fields.CharField(max_length=1026, unique=True), 'Must be unique')
    error_id = D(fields.IntegerField(), 'The id of the content error')
    
    # SyntheticFields, fields w/o corresponding db column
    content_source_type = modellib.SyntheticField() # fk

    
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

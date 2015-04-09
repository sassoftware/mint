#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
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
    upstream_url = D(models.TextField(), "Upstream repository URL used when creating external project for this platform")
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


class PlatformBuildTemplates(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['platform_build_template']
    
    
class PlatformBuildTemplate(modellib.XObjIdModel):
    class Meta:
        abstract = True
    pass


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# Image models -- may be heavily in flux as Target service evolves
# or may be replaced by target service.  Don't get attached.
# **THESE ARE CURRENTLY JUST STUBS TO UNBLOCK DEVELOPMENT**

import datetime
from dateutil import tz

from django.db import models
from mint import helperfuncs
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj
from conary import trovetup
from conary import versions
from conary.deps import deps
import sys

APIReadOnly = modellib.APIReadOnly

class Images(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['image']
    _xobj = xobj.XObjMetadata(tag='images')
    
    actions = D(modellib.SyntheticField('jobs.Actions'),
        "actions available on the images")

    def get_url_key(self, *args, **kwargs):
        return self.url_key


class Image(modellib.XObjIdModel):
    class Meta:
        db_table = u'builds'

    _xobj_hidden_accessors = set(['builddata_set'])

    def __unicode__(self):
        return self.name

    image_id = models.AutoField(primary_key=True, db_column='buildid')
    project = modellib.DeferredForeignKey('projects.Project', db_column='projectid',
        related_name="images", view_name="ProjectImages")
    #The images need to be linked to the project branch stages and the project
    #Until then, hide project_branch_stage
    project_branch_stage = modellib.XObjHidden(
        modellib.DeferredForeignKey('projects.Stage', db_column='stageid',
        related_name="images", view_name="ProjectBranchStageImages", null=True))
    release = models.ForeignKey('Release', null=True,
        db_column='pubreleaseid')
    image_type = models.IntegerField(db_column="buildtype")
    job_uuid = models.CharField(max_length=64, null=True)
    name = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    trove_name = models.CharField(max_length=128, null=True,
        db_column='trovename')
    trove_version = models.CharField(max_length=255, null=True,
        db_column='troveversion')
    trove_flavor = models.CharField(max_length=4096, null=True,
        db_column='troveflavor')
    trove_last_changed = models.DecimalField(max_digits=14,
        decimal_places=3, null=True, db_column='trovelastchanged')
    output_trove = models.TextField(null=True)
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timecreated')
    created_by = modellib.ForeignKey('users.User',
        db_column='createdby',null=True, related_name='created_images')
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeupdated')
    updated_by = modellib.ForeignKey('users.User', db_column='updatedby',
        related_name='updated_images', null=True)
    image_count = models.IntegerField(null=True, default=0,
        db_column="buildcount")
    project_branch = models.ForeignKey('projects.ProjectVersion', null=True,
        related_name="images",
        db_column='productversionid')
    stage_name = models.CharField(max_length=255, db_column='stagename',
        null=True, blank=True, default='')
    status = models.IntegerField(null=True, default=-1)
    status_message = models.TextField(null=True, blank=True, default='',
        db_column="statusmessage")
    metadata = modellib.SyntheticField()
    architecture = modellib.SyntheticField()
    trailing_version = modellib.SyntheticField()
    released = modellib.SyntheticField()
    num_image_files = modellib.SyntheticField()
    #actions = modellib.SyntheticField()
        
    def computeSyntheticFields(self, sender, **kwargs):
        self._computeMetadata()
        
        if self.trove_flavor is not None:
            self.architecture = helperfuncs.getArchFromFlavor(str(self.trove_flavor))
            
        if self.trove_version is not None:
            tv_obj = helperfuncs.parseVersion(self.trove_version)
            if tv_obj is not None:
                self.trailing_version = str(tv_obj.trailingRevision())

        if self.release is not None:
            self.released = True
        else:
            self.released = False
            
        if self.image_files is not None:
            self.num_image_files = len(self.image_files.all())
        else:
            self.num_image_files = 0;

    def _computeMetadata(self):
        if self._rbmgr is None or self.output_trove is None:
            return
        troveTup = self._getOutputTrove()
        reposMgr = self._rbmgr.restDb.productMgr.reposMgr
        metadata = reposMgr.getKeyValueMetadata([troveTup])[0]
        if metadata is None:
            self.metadata = None
            return
        metaxml = xobj.XObj()
        for key, value in metadata.items():
            setattr(metaxml, key, value)
        self.metadata = metaxml

    def saveMetadata(self):
        if (self._rbmgr is None or self.output_trove is None
                or self.metadata is None):
            return
        # Commit a new image trove with updated metadata to repository and save
        # its NVF back to the output_trove field.
        metadata = self._getMetadataDict()
        oldTup = self._getOutputTrove()
        reposMgr = self._rbmgr.restDb.productMgr.reposMgr
        newTup = reposMgr.updateKeyValueMetadata([(oldTup, metadata)],
                admin=True)[0]
        self.output_trove = newTup.asString()
        self.save()
        # Log new image tuple
        msg = "Updated image committed as %s=%s/%s" % (newTup.name,
                newTup.version.trailingLabel(),
                newTup.version.trailingRevision())
        self._rbmgr.restDb.imageMgr._getImageLogger(self.project.short_name,
                self.image_id).info(msg)

    def _getOutputTrove(self):
        if self.output_trove is None:
            return None
        name, version, flavor = trovetup.TroveSpec.fromString(self.output_trove)
        version = versions.VersionFromString(version)
        if flavor is None:
            flavor = deps.Flavor()
        return trovetup.TroveTuple(name, version, flavor)

    def _getMetadataDict(self):
        if self.metadata is None:
            return None
        metadataDict = {}
        for name, value in self.metadata.__dict__.items():
            if name.startswith('_'):
                continue
            metadataDict[name] = str(value)
        return metadataDict
    
    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        # Convert timestamp fields in the database to our standard UTC format
        if xobjModel.time_created:
            xobjModel.time_created = str(datetime.datetime.fromtimestamp(
                xobjModel.time_created, tz.tzutc()))
        if xobjModel.time_updated:
            xobjModel.time_updated = str(datetime.datetime.fromtimestamp(
                xobjModel.time_updated, tz.tzutc()))
        return xobjModel


class Releases(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ['release']
    _xobj = xobj.XObjMetadata(tag='releases')        


class Release(modellib.XObjIdModel):
    class Meta:
        db_table = u'publishedreleases'

    _xobj = xobj.XObjMetadata(
        tag='release')
    _xobj_hidden_accessors = set(['image_set'])

    release_id = models.AutoField(primary_key=True,
        db_column='pubreleaseid')
    project = modellib.DeferredForeignKey('projects.Project', db_column='projectid', 
        related_name='releases')
    name = models.CharField(max_length=255, blank=True, default='')
    version = models.CharField(max_length=32, blank=True, default='')
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timecreated', null=True)
    created_by = modellib.ForeignKey('users.User', db_column='createdby',
        related_name='created_releases', null=True)
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeupdated')
    updated_by = modellib.ForeignKey('users.User', db_column='updatedby',
        related_name='updated_releases', null=True)
    time_published = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timepublished', null=True)
    published_by = modellib.ForeignKey('users.User', 
        db_column='publishedby', related_name='published_releases',
        null=True)
    should_mirror = models.SmallIntegerField(db_column='shouldmirror',
        blank=True, default=0)
    time_mirrored = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timemirrored')  


class BuildFiles(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='image_files')
    list_fields = ['image_file']
    
    
class BuildFile(modellib.XObjIdModel):
    class Meta:
        db_table = 'buildfiles'
    
    _xobj = xobj.XObjMetadata(tag='image_file')
    
    
    file_id = models.AutoField(primary_key=True, db_column='fileid')
    image = models.ForeignKey('Image', null=False, db_column='buildid', related_name='image_files')
    idx = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=255, null=False, default='')
    size = models.IntegerField()
    sha1 = models.CharField(max_length=40)


class BuildData(modellib.XObjIdModel):
    class Meta:
        db_table = 'builddata'
        unique_together = ('build', 'name')
    
    build_data_id = models.AutoField(primary_key=True, db_column='builddataid')
    build = models.ForeignKey('Image', db_column='buildid')
    name = models.CharField(max_length=32, null=False)
    value = models.TextField()
    data_type = models.SmallIntegerField(null=False, db_column='datatype')
    

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj   

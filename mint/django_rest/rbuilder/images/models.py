#
# Copyright (c) 2010 rPath, Inc.
#
# All Rights Reserved
#

# Image models -- may be heavily in flux as Target service evolves
# or may be replaced by target service.  Don't get attached.
# **THESE ARE CURRENTLY JUST STUBS TO UNBLOCK DEVELOPMENT**

from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj

APIReadOnly = modellib.APIReadOnly

class Images(modellib.Collection):

    # XSL = 'fixme.xsl' # TODO
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag = 'images')
    list_fields = ['image']
    grant = []
    objects = modellib.RbacPermissionsManager()
    view_name = 'Images'

    def __init__(self):
        modellib.Collection.__init__(self)

    def save(self):
        return [s.save() for s in self.image]

################################################
# WHAT IS THIS?  IT's JUST A PLACEHOLDER
#
# THIS SHOULD PROBABLY BE / MERGE WITH OUR MODEL
# OF A UNIFIED TABLE that contains images
# from targets (target service) as well as 
# ones we can deploy
#
#  V V V V V V V V V V V V V V V V V V V V 
################################################

class Image(modellib.XObjIdModel):
    
    # XSL = "fixme.xsl" # TODO

    class Meta:
        # db_table = 'to_be_determined'
        abstract = True

    view_name = 'Image'

    _xobj = xobj.XObjMetadata(
        tag = 'image'
    )
    _xobj_hidden_accessors = set([])
    summary_view = []

    id = D(models.AutoField(primary_key=True),
        "the database ID for the permission")
    name = D(models.TextField(), 
        "the database ID for the permission")

class PublishedReleases(modellib.Collection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='published_releases')
    list_fields = ['published_release']
    
    
class PublishedRelease(modellib.XObjIdModel):
    class Meta:
        db_table = 'PublishedReleases'
        
    pub_release_id = models.AutoField(primary_key=True, db_column='pubreleaseid')
    project_id = models.ForeignKey('projects.Project', null=False, db_column='projectid')
    name = models.CharField(max_length=255, null=False, default='')
    version = models.CharField(max_length=32, null=False, default='')
    description = models.TextField()
    time_created = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    created_by = models.ForeignKey('users.User', db_column='createdby')
    time_updated = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timeupdated')
    updated_by = models.ForeignKey('users.User', db_column='updatedby')
    time_published = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timepublished')
    published_by = models.ForeignKey('users.User', db_column='publishedby')
    should_mirror = models.IntegerField(null=False, default=0, db_column='shouldmirror')
    time_mirrored = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timemirrored')


class Builds(modellib.XObjCollection):
    class Meta:
        abstract = True
        
    list_fields = ['build']
    

class Build(modellib.XObjIdModel):
    class Meta:
        db_table = 'builds'
    
    build_id = models.AutoField(primary_key=True, db_column='buildid')
    project_id = models.ForeignKey('projects.Project', db_column='projectid', null=False)
    stage_id = models.ForeignKey('projects.Stage')
    pub_release_id = models.ForeignKey('PublishedRelease', db_column='pubreleaseid')
    build_type = models.IntegerField(db_column='buildtype')
    job_uuid = models.IntegerField() # is of type 'uuid' in schema
    name = models.CharField(max_length=255)
    description = models.TextField()
    trove_name = models.CharField(max_length=128, db_column='trovename')
    trove_version = models.CharField(max_length=255, db_column='troveversion')
    trove_flavor = models.CharField(max_length=4096, db_column='troveflavor')
    trove_last_changed = modellib.DecimalField(
        max_digits=14, decimal_places=3, db_column='trovelastchanged')
    time_created = modellib.DateTimeUtcField(
        max_digits=14, decimal_places=3, db_column='timecreated')
    created_by = models.ForeignKey('users.User', db_column='createdby')
    time_updated = modellib.DecimalField(
        max_digits=14, decimal_places=3, db_column='timeupdated')
    updated_by = models.ForeignKey('users.User', db_column='updatedby')
    build_count = models.IntegerField(null=False, default=0, db_column='buildcount')
    product_version_id = models.ForeignKey('projects.ProjectVersion', db_column='productversionid')
    stage_name = models.CharField(max_length=255, default='', db_column='stagename')
    status = models.IntegerField(default=-1)
    status_message = models.TextField(default='', db_column='statusmessage')
    output_trove = models.TextField()



class BuildFiles(modellib.XObjCollection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='build_files')
    list_fields = 'build_file'
    
    
class BuildFile(modellib.XObjIdModel):
    class Meta:
        db_table = 'buildfiles'
        
    file_id = models.AutoField(primary_key=True, db_column='fileid')
    build_id = models.ForeignKey('Build', null=False, db_column='buildid')
    idx = models.IntegerField(null=False, default=0)
    title = models.CharField(max_length=255, null=False, default='')
    size = models.IntegerField()
    sha1 = models.CharField(max_length=40)
    
    
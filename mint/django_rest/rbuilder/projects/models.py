#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys

from django.db import models

from mint import userlevels
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usermodels

from xobj import xobj

class Projects(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "projects")
    view_name = "Projects"
    list_fields = ["project"]
    project = []

class Project(modellib.XObjIdModel):
    class Meta:
        db_table = u"projects"
        
    _xobj_hidden_accessors = set(['membership'])
    view_name = "Project"
    url_key = ["short_name"]
    
    project_id = models.AutoField(primary_key=True, db_column="projectid",
        blank=True)
    hostname = models.CharField(unique=True, max_length=63)
    name = models.CharField(unique=True, max_length=128)
    namespace = models.CharField(max_length=16, null=True)
    domain_name = models.CharField(max_length=128, db_column="domainname")
    short_name = models.CharField(unique=True, max_length=63, 
        db_column="shortname")
    project_url = models.CharField(max_length=128, blank=True,
        db_column= "projecturl")
    repository_hostname = models.CharField(max_length=255, db_column="fqdn")
    description = models.TextField(null=True, blank=True)
    project_type = models.CharField(max_length=128, db_column="prodtype")
    commit_email = models.CharField(max_length=128, null=True, blank=True, 
        db_column="commitemail")
    backup_external = models.SmallIntegerField(default=0,
        db_column="backup_external")
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timecreated")
    time_modified = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timemodified")
    hidden = models.SmallIntegerField(default=0)
    creator = models.ForeignKey(usermodels.User,
        related_name="creator", null=True, db_column="creatorid")
    external = models.SmallIntegerField(default=0)
    disabled = models.SmallIntegerField(default=0)
    isAppliance = models.SmallIntegerField(default=1)
    version = models.CharField(max_length=128, null=True, blank=True,
        default='')
    database = models.CharField(max_length=128, null=True)
    members = modellib.DeferredManyToManyField(usermodels.User, 
        through="Member")

    def __unicode__(self):
        return self.hostname
        
    def serialize(self, request):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        member = self.membership.filter(user=request._authUser)
        if member:
            role = member[0].level
            xobjModel.role = role
        return xobjModel

class Members(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ["member"]
    member = []
    view_name = "ProjectMembers"

class Member(modellib.XObjModel):
    project = models.ForeignKey(Project, db_column='projectid',
        related_name='membership')
    user = modellib.DeferredForeignKey(usermodels.User, db_column='userid',
        related_name='project_membership')
    level = models.SmallIntegerField()
    class Meta:
        db_table = u'projectusers'

class Versions(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "versions")
    view_name = "ProjectVersions"
    list_fields = ["version"]
    version = []

class Version(modellib.XObjIdModel):
    class Meta:
        db_table = u'productversions'

    _xobj_hidden_accessors = set(['stages',])
    _xobj = xobj.XObjMetadata(
        tag="version")
    view_name = 'ProjectVersion'
    url_key = ['project', 'pk']

    version_id = models.AutoField(primary_key=True,
        db_column='productversionid')
    project = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="versions", view_name="ProjectVersions",
        ref_name="id")
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column="timecreated")

    def __unicode__(self):
        return self.name
        
class Stage(modellib.XObjIdModel):
    class Meta:
        db_table = 'inventory_stage'

    view_name = 'ProjectVersionStage'
    _xobj = xobj.XObjMetadata(tag='stage')
    _xobj_hidden_accessors = set(['version_set',])

    stage_id = models.AutoField(primary_key=True)
    major_version = modellib.DeferredForeignKey(Version, related_name="stages")
    name = models.CharField(max_length=256)
    label = models.TextField(unique=True)

    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model._xobj.text = self.name
        return xobj_model

class Release(modellib.XObjModel):
    class Meta:
        db_table = u'publishedreleases'

    _xobj = xobj.XObjMetadata(
        tag='releases')
    view_name = "ProjectRelease"
     
    release_id = models.AutoField(primary_key=True)
    project = modellib.DeferredForeignKey(Project, db_column='projectid', 
        related_name='releases')
    name = models.CharField(max_length=255, blank=True, default='')
    version = models.CharField(max_length=32, blank=True, default='')
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timeCreated', null=True)
    created_by = modellib.ForeignKey(usermodels.User, db_column='createdby',
        related_name='created_releases', null=True)
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeUpdated')
    updated_by = modellib.ForeignKey(usermodels.User, db_column='updatedby',
        related_name='updated_releases', null=True)
    time_published = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timePublished', null=True)
    published_by = modellib.ForeignKey(usermodels.User, 
        db_column='publishedby', related_name='published_releases',
        null=True)
    should_mirror = models.SmallIntegerField(db_column='shouldMirror',
        blank=True, default=0)
    time_mirrored = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeMirrored')
               
class Image(modellib.XObjIdModel):
    class Meta:
        db_table = u'builds'
        
    _xobj = xobj.XObjMetadata(
        tag="image")
    view_name = "ProjectImage"

    def __unicode__(self):
        return self.name

    image_id = models.AutoField(primary_key=True, db_column='buildid')
    project = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="images", view_name="ProjectImages", ref_name="id")
    release = models.ForeignKey(Release, null=True,
        db_column='pubreleaseid')
    build_type = models.IntegerField(db_column="buildType")
    job_uuid = models.CharField(max_length=64, null=True)
    name = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    trove_name = models.CharField(max_length=128, null=True,
        db_column='troveName')
    trove_version = models.CharField(max_length=255, null=True,
        db_column='troveVersion')
    trove_flavor = models.CharField(max_length=4096, null=True,
        db_column='troveFlavor')
    trove_last_changed = models.DecimalField(max_digits=14,
        decimal_places=3, null=True, db_column='troveLastChanged')
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timeCreated')
    created_by = modellib.ForeignKey(usermodels.User,
        db_column='createdby', related_name='created_images')
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeUpdated')
    updated_by = modellib.ForeignKey(usermodels.User, db_column='updatedby',
        related_name='updated_images', null=True)
    build_count = models.IntegerField(null=True, default=0)
    version = models.ForeignKey(Version, null=True,
        db_column='productversionid')
    stage_name = models.CharField(max_length=255, db_column='stageName',
        null=True, blank=True, default='')
    status = models.IntegerField(null=True, default=-1)
    status_message = models.TextField(null=True, blank=True, default='',
        db_column='')

class Downloads(modellib.XObjModel):
    class Meta:
        db_table = u'urldownloads'

    imageId = models.ForeignKey(Image, db_column='urlid')
    timedownloaded = models.CharField(max_length=14)
    ip = models.CharField(max_length=64)
    
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj

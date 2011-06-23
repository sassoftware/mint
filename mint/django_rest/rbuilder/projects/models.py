#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import datetime
import sys
import time
from dateutil import tz

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
        
    _xobj = xobj.XObjMetadata(tag='project')
    _xobj_hidden_accessors = set(['membership', 'package_set', 
        'platform_set', 'productplatform_set', 'abstractplatform_set'])
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
    project_type = models.CharField(max_length=128, db_column="prodtype",
        default="Appliance")
    commit_email = models.CharField(max_length=128, null=True, blank=True, 
        db_column="commitemail")
    backup_external = models.SmallIntegerField(default=0,
        db_column="backupexternal")
    created_date = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timecreated")
    modified_date = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timemodified")
    hidden = models.SmallIntegerField(default=0)
    creator = models.ForeignKey(usermodels.User,
        related_name="creator", null=True, db_column="creatorid")
    external = models.SmallIntegerField(default=0)
    disabled = models.SmallIntegerField(default=0)
    is_appliance = models.SmallIntegerField(default=1, db_column="isappliance")
    version = models.CharField(max_length=128, null=True, blank=True,
        default='')
    database = models.CharField(max_length=128, null=True)
    members = modellib.DeferredManyToManyField(usermodels.User, 
        through="Member")

    load_fields = [ short_name ]

    def __unicode__(self):
        return self.hostname
        
    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        if request is not None:
            member = self.membership.filter(user=request._authUser)
            if member:
                role = userlevels.names[member[0].level]
                xobjModel.role = role
        xobjModel.is_appliance = bool(self.is_appliance)
        xobjModel.hidden = bool(self.hidden)
        xobjModel.external = bool(self.external)

        # Convert timestamp fields in the database to our standard UTC format
        xobjModel.created_date = str(datetime.datetime.fromtimestamp(
            xobjModel.created_date, tz.tzutc()))
        xobjModel.modified_date = str(datetime.datetime.fromtimestamp(
            xobjModel.modified_date, tz.tzutc()))
        return xobjModel

    def setIsAppliance(self):
        if self.project_type == "Appliance" or \
           self.project_type == "PlatformFoundation":
            self.is_appliance = 1
        else:
            self.is_appliance = 0

    def save(self, *args, **kwargs):
        # Default project type to Appliance
        if self.project_type is None:
            self.project_type = "Appliance"

        self.setIsAppliance()

        if self.created_date is None:
            self.created_date = str(time.time())
        if self.modified_date is None:
            self.modified_date = str(time.time())
        return modellib.XObjIdModel.save(self, *args, **kwargs)

class Members(modellib.Collection):
    class Meta:
        abstract = True

    list_fields = ["member"]
    member = []
    view_name = "ProjectMembers"

class Member(modellib.XObjModel):
    project = models.ForeignKey(Project, db_column='projectid',
        related_name='membership', primary_key=True)
    user = modellib.DeferredForeignKey(usermodels.User, db_column='userid',
        related_name='project_membership')
    level = models.SmallIntegerField()
    class Meta:
        db_table = u'projectusers'

class ProjectVersions(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "project_branches")
    view_name = "ProjectVersions"
    list_fields = ["project_branch"]
    version = []

class ProjectVersion(modellib.XObjIdModel):
    class Meta:
        db_table = u'productversions'

    _xobj = xobj.XObjMetadata(
        tag="project_branch")
    view_name = 'ProjectVersion'

    branch_id = models.AutoField(primary_key=True,
        db_column='productversionid')
    project = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="project_branches", view_name="ProjectVersions", null=True)
    project_name = modellib.SyntheticField()
    project_external = modellib.SyntheticField()
    project_short_name = modellib.SyntheticField()
    project_type = modellib.SyntheticField()
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    created_date = models.DecimalField(max_digits=14, decimal_places=3,
        db_column="timecreated")

    def __unicode__(self):
        return self.name
        
    def save(self, *args, **kwargs):
        if self.created_date is None:
            self.created_date = str(time.time())
        return modellib.XObjIdModel.save(self, *args, **kwargs)

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        # Convert timestamp fields in the database to our standard UTC format
        xobjModel.created_date = str(datetime.datetime.fromtimestamp(
            xobjModel.created_date, tz.tzutc()))
        xobjModel.project_name = self.project.name
        xobjModel.project_type = self.project.project_type
        xobjModel.project_external = self.project.external
        xobjModel.project_short_name = self.project.short_name
        return xobjModel

class Stages(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "project_branch_stages")
    view_name = "ProjectStages"
    list_fields = ["project_branch_stage"]
    project_branch_stage = []

class Stage(modellib.XObjIdModel):
    class Meta:
        db_table = 'project_branch_stage'

    view_name = 'ProjectStage'
    _xobj = xobj.XObjMetadata(tag='project_branch_stage')
    _xobj_hidden_accessors = set(['version_set',])

    stage_id = models.AutoField(primary_key=True)
    project_branch = modellib.DeferredForeignKey(ProjectVersion, 
        related_name="stages", view_name="ProjectBranchStages")
    name = models.CharField(max_length=256)
    label = models.TextField(unique=True)
    promotable = models.BooleanField(default=False)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)

    def serialize(self, request=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model._xobj.text = self.name
        xobj_model.hostname = self.project_branch.project.hostname
        return xobj_model

class Release(modellib.XObjModel):
    class Meta:
        db_table = u'publishedreleases'

    _xobj = xobj.XObjMetadata(
        tag='releases')
    view_name = "ProjectRelease"
     
    release_id = models.AutoField(primary_key=True,
        db_column='pubreleaseid')
    project = modellib.DeferredForeignKey(Project, db_column='projectid', 
        related_name='releases')
    name = models.CharField(max_length=255, blank=True, default='')
    version = models.CharField(max_length=32, blank=True, default='')
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timecreated', null=True)
    created_by = modellib.ForeignKey(usermodels.User, db_column='createdby',
        related_name='created_releases', null=True)
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeupdated')
    updated_by = modellib.ForeignKey(usermodels.User, db_column='updatedby',
        related_name='updated_releases', null=True)
    time_published = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timepublished', null=True)
    published_by = modellib.ForeignKey(usermodels.User, 
        db_column='publishedby', related_name='published_releases',
        null=True)
    should_mirror = models.SmallIntegerField(db_column='shouldmirror',
        blank=True, default=0)
    time_mirrored = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timemirrored')
               
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
        related_name="images", view_name="ProjectImages")
    release = models.ForeignKey(Release, null=True,
        db_column='pubreleaseid')
    build_type = models.IntegerField(db_column="buildtype")
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
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column='timecreated')
    created_by = modellib.ForeignKey(usermodels.User,
        db_column='createdby', related_name='created_images')
    time_updated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True, db_column='timeupdated')
    updated_by = modellib.ForeignKey(usermodels.User, db_column='updatedby',
        related_name='updated_images', null=True)
    build_count = models.IntegerField(null=True, default=0,
        db_column="buildcount")
    version = models.ForeignKey(ProjectVersion, null=True,
        related_name="images",
        db_column='productversionid')
    stage_name = models.CharField(max_length=255, db_column='stagename',
        null=True, blank=True, default='')
    status = models.IntegerField(null=True, default=-1)
    status_message = models.TextField(null=True, blank=True, default='',
        db_column="statusmessage")

class Downloads(modellib.XObjModel):
    class Meta:
        db_table = u'urldownloads'

    imageId = modellib.DeferredForeignKey(Image, db_column='urlid')
    timedownloaded = models.CharField(max_length=14)
    ip = models.CharField(max_length=64)
    
class InboundMirror(modellib.XObjModel):
    _xobj = xobj.XObjMetadata(tag="inbound_mirror")
    class Meta:
        db_table = "inboundmirrors"

    inbound_mirror_id = models.AutoField(primary_key=True,
        db_column="inboundmirrorid")
    target_project = modellib.ForeignKey(Project,
        related_name="inbound_mirrors",
        db_column="targetprojectid")
    source_labels = models.CharField(max_length=767,
        db_column="sourcelabels")
    source_url = models.CharField(max_length=767,
        db_column="sourceurl")
    source_auth_type = models.CharField(max_length=32,
        db_column="sourceauthtype")
    source_user_name = models.CharField(max_length=254, null=True,
        db_column="sourceusername")
    source_password = models.CharField(max_length=254, null=True,
        db_column="sourcepassword")
    source_entitlement = models.CharField(max_length=254, null=True,
        db_column="sourceentitlement")
    mirror_order = models.IntegerField(default=0, null=True,
        db_column="mirrororder")
    all_labels = models.IntegerField(default=0, null=True,
        db_column="alllabels")

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj

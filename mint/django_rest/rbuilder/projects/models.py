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
# from mint.django_rest.rbuilder.platforms import models as platformsmodels
from xobj import xobj


class Groups(modellib.XObjModel):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='troves')
        
    list_fields = ['group']


class Group(modellib.XObjIdModel):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='trove', attributes={'href':str})
    
    group_id = models.AutoField(primary_key=True)
    hostname = models.CharField(max_length=1026)
    name = models.CharField(max_length=1026)
    version = models.CharField(max_length=1026)
    label = models.CharField(max_length=1026)
    trailing = models.CharField(max_length=1026)
    flavor = models.TextField()
    time_stamp = models.DecimalField()
    # images = modellib.DeferredForeignKey('Image')
    image_count = models.IntegerField()
    
    def __init__(self, href=None):
        if href:
            self.href = href
    

class Projects(modellib.Collection):
    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
                tag = "projects")
    view_name = "Projects"
    list_fields = ["project"]
    project = []

class PlatformHref(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='platform')

class Project(modellib.XObjIdModel):
    class Meta:
        db_table = u"projects"

    _xobj = xobj.XObjMetadata(tag='project')
    _xobj_hidden_accessors = set(['membership', 'package_set', 
        'platform_set', 'productplatform_set', 'abstractplatform_set', 'labels'])
    view_name = "Project"
    url_key = ["short_name"]
    summary_view = ["name", "short_name", "domain_name"]
    
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
    backup_external = models.BooleanField(default=False,
        db_column="backupexternal")
    created_date = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timecreated")
    modified_date = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timemodified")
    hidden = models.BooleanField(default=False)
    creator = models.ForeignKey(usermodels.User,
        related_name="creator", null=True, db_column="creatorid")
    external = models.BooleanField(default=False)
    disabled = models.BooleanField(default=False)
    is_appliance = models.BooleanField(default=True, db_column="isappliance")
    version = models.CharField(max_length=128, null=True, blank=True,
        default='')
    database = models.CharField(max_length=128, null=True)
    members = modellib.DeferredManyToManyField(usermodels.User, 
        through="Member")
    
    # synthetic properties hoisted from labels - these will eventually be merged
    # into the projects schema instead of a labels table
    upstream_url = modellib.SyntheticField()
    auth_type = modellib.SyntheticField()
    user_name = modellib.SyntheticField()
    password = modellib.SyntheticField()
    entitlement = modellib.SyntheticField()
    actions = modellib.SyntheticField()

    load_fields = [ short_name ]

    _ApplianceTypes = set([ "Appliance", "PlatformFoundation", ])

    def __unicode__(self):
        return self.hostname

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        if request is not None:
            member = self.membership.filter(user=request._authUser)
            if member:
                role = userlevels.names[member[0].level]
                xobjModel.role = role
                
        # Convert timestamp fields in the database to our standard UTC format
        xobjModel.created_date = str(datetime.datetime.fromtimestamp(
            xobjModel.created_date, tz.tzutc()))
        xobjModel.modified_date = str(datetime.datetime.fromtimestamp(
            xobjModel.modified_date, tz.tzutc()))

        # Attach URL and auth data from Labels if and only if this is a
        # proxy-mode external project. Otherwise these fields are meaningless.
        if not self.database:
            labels = self.labels.all()
            if labels:
                label = labels[0]
                xobjModel.upstream_url = label.url
                xobjModel.auth_type = label.auth_type
                xobjModel.user_name = label.user_name
                xobjModel.password = label.password
                xobjModel.entitlement = label.entitlement
        return xobjModel

    def setIsAppliance(self):
        self.is_appliance = (self.project_type in self._ApplianceTypes)

    @classmethod
    def Now(cls):
        return "%.2f" % time.time()

    def save(self, *args, **kwargs):
        # Default project type to Appliance
        if self.project_type is None:
            self.project_type = "Appliance"
        if not self.project_url:
            self.project_url = ''

        self.setIsAppliance()

        if not self.hostname:
            self.hostname = self.short_name

        now = self.Now()
        if self.created_date is None:
            self.created_date = now
        if self.modified_date is None:
            self.modified_date = now

        if not self.repository_hostname and self.hostname and self.domain_name:
            self.repository_hostname = '%s.%s' % (self.hostname, self.domain_name)

        labels = self.labels.all()
        if labels:
            label = labels[0]
            if self.database:
                # Internal projects and mirror projects have no use for these
                # fields so make sure they are nulled out.
                label.url = None
                label.auth_type = 'none'
                label.user_name = None
                label.password = None
                label.entitlement = None
            else:
                assert self.external
                label.url = self.upstream_url
                label.auth_type = self.auth_type
                label.user_name = self.user_name
                label.password = self.password
                label.entitlement = self.entitlement
            # This field doesn't mean anything but some old code might still
            # use it.
            label.label = self.repository_hostname + '@dummy:label'
            label.save()

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
    # a.k.a. "branch"
    class Meta:
        db_table = u'productversions'

    _xobj = xobj.XObjMetadata(
        tag="project_branch")
    
    view_name = 'ProjectVersion'
    summary_view = ["name"]

    branch_id = models.AutoField(primary_key=True,
        db_column='productversionid')
    project = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="project_branches", view_name="ProjectVersions", null=True)
    label = models.TextField(unique=True, null=False)
    cache_key = modellib.XObjHidden(models.TextField(null=True))
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    created_date = models.DecimalField(max_digits=14, decimal_places=3,
        db_column="timecreated")

    platform_label = modellib.SyntheticField() # don't think this is needed if we already have a platform
    images = modellib.SyntheticField()
    definition = modellib.SyntheticField()
    platform = modellib.SyntheticField()
    platform_version = modellib.SyntheticField()
    image_type_definitions = modellib.SyntheticField()
    source_group = modellib.SyntheticField() # not implemented yet

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.created_date is None:
            self.created_date = Project.Now()
        return modellib.XObjIdModel.save(self, *args, **kwargs)

    def serialize(self, request=None):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        # Convert timestamp fields in the database to our standard UTC format
        xobjModel.created_date = str(datetime.datetime.fromtimestamp(
            xobjModel.created_date, tz.tzutc()))
        return xobjModel

    # def computeSyntheticFields(self, sender, **kwargs):
    #     if self._rbmgr is None or self.project_id is None:
    #         return
    #     restDb = self._rbmgr.restDb
    #     plat = restDb.getProductVersionPlatform(self.project.repository_hostname, self.name)
    #     self.platform_label = plat.label


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
    _xobj = xobj.XObjMetadata(tag='project_branch_stage', elements = ['labels', ])
    _xobj_hidden_accessors = set(['version_set',])
    
    summary_view = ["name"]

    stage_id = models.AutoField(primary_key=True)
    project = modellib.DeferredForeignKey(Project,
        related_name="project_branch_stages", view_name="ProjectBranchStages")
    project_branch = modellib.DeferredForeignKey(ProjectVersion, 
        related_name="project_branch_stages", view_name="ProjectBranchStages")
    name = models.CharField(max_length=256)
    label = models.TextField(null=False)
    promotable = models.BooleanField(default=False)
    created_date = modellib.DateTimeUtcField(auto_now_add=True)
    groups = modellib.SyntheticField()

    def serialize(self, request=None):
        # FIXME TOTAL HACK, import statement inlined because of some undiscovered conflict
        from mint.django_rest.rbuilder.projects import views as projectsviews
        view = projectsviews.GroupsService()
        stages = xobj.parse(view.get(request).content)
        # self.groups = [Group(href=s.groups.href) for s in stages.stages.stage]
        self.groups = Groups()
        groups = [Group(href=s.groups.href) for s in stages.stages.stage]
        self.groups.group = groups
        xobjModel = modellib.XObjModel.serialize(self, request)
        return xobjModel
        
    
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
               
             
class Images(modellib.Collection):
    class Meta:
        abstract = True
        
    list_fields = ['image']
    _xobj = xobj.XObjMetadata(tag='images')
             
               
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
    #The images need to be linked to the project branch stages and the project     
    project_branch_stage = modellib.DeferredForeignKey(Stage, db_column='stageid',
        related_name="images", view_name="ProjectImages", null=True)
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
        related_name="project_version",
        db_column='productversionid')
    stage_name = models.CharField(max_length=255, db_column='stagename',
        null=True, blank=True, default='')
    status = models.IntegerField(null=True, default=-1)
    status_message = models.TextField(null=True, blank=True, default='',
        db_column="statusmessage")
    actions = modellib.SyntheticField()


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

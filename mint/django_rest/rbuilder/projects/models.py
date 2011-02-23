#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models

from mint import userlevels
from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder import models as rbuildermodels

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
    _xobj_hidden_accessors = set(['project_members'])
    view_name = "Project"
    url_key = "short_name"
    
    project_id = models.AutoField(primary_key=True, db_column="projectid",
        blank=True)
    hostname = models.CharField(unique=True, max_length=63)
    name = models.CharField(unique=True, max_length=128)
    namespace = models.CharField(max_length=16, null=True)
    domain_name = models.CharField(max_length=128, db_column="domainname")
    short_name = models.CharField(unique=True, max_length=63, 
        db_column="shortname")
    project_url = models.CharField(max_length=128, null=True, blank=True,
        db_column= "projecturl")
    repository_hostname = models.CharField(max_length=255, db_column="fqdn")
    description = models.TextField(null=True, blank=True)
    project_type = models.CharField(max_length=128, db_column="prodtype")
    commit_email = models.CharField(max_length=128, null=True, blank=True, 
        db_column="commitemail")
    backup_external = models.SmallIntegerField(null=True, blank=True,
        db_column="backup_external")
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timecreated")
    time_modified = models.DecimalField(max_digits=14, decimal_places=3,
        blank=True, db_column="timemodified")
    hidden = models.SmallIntegerField()
    creator = models.ForeignKey(rbuildermodels.Users,
        related_name="creator", null=True, db_column="creatorid")
    members = models.ManyToManyField(rbuildermodels.Users, through="Member")
        
    
    class Meta:
        db_table = u"projects"
        
    def __unicode__(self):
        return self.hostname
        
    def serialize(self, request):
        xobjModel = modellib.XObjIdModel.serialize(self, request)
        member = self.membership.filter(user=request._authUser)
        if member:
            role = member[0].level
            xobjModel.role = role
        return xobjModel

class Member(modellib.XObjModel):
    project = models.ForeignKey(Project, db_column='projectid',
        related_name='membership')
    user = models.ForeignKey(rbuildermodels.Users, db_column='userid',
        related_name='project_membership')
    level = models.SmallIntegerField()
    class Meta:
        db_table = u'projectusers'

class Version(modellib.XObjIdModel):
    class Meta:
        db_table = u'productversions'

    _xobj = xobj.XObjMetadata(
        tag="version")

    view_name = 'ProjectVersions'

    def __unicode__(self):
        return self.name
        
    productVersionId = models.AutoField(primary_key=True,
        db_column='productversionid')
    productId = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="versions")
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3,
        db_column="timecreated")

class Releases(modellib.XObjModel):
    pubreleaseid = models.AutoField(primary_key=True)
    productId = modellib.DeferredForeignKey(Project, db_column='projectid', 
        related_name='releasesProduct')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32)
    description = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(rbuildermodels.Users, db_column='createdby',
        related_name='releaseCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3)
    updatedby = models.ForeignKey(rbuildermodels.Users, db_column='updatedby',
        related_name='releaseUpdater')
    timepublished = models.DecimalField(max_digits=14, decimal_places=3)
    publishedby = models.ForeignKey(rbuildermodels.Users, db_column='publishedby',
        related_name='releasePublisher')
    shouldmirror = models.SmallIntegerField()
    timemirrored = models.DecimalField(max_digits=14, decimal_places=3)
    class Meta:
        db_table = u'publishedreleases'
     
    def __unicode__(self):
        return self.name
               
class Image(modellib.XObjIdModel):
    class Meta:
        db_table = u'builds'
        
    _xobj = xobj.XObjMetadata(
        tag="image")

    view_name = "ProjectImage"

    def __unicode__(self):
        return self.name

    imageId = models.AutoField(primary_key=True, db_column='buildid')
    productId = modellib.DeferredForeignKey(Project, db_column='projectid',
        related_name="images")
    pubreleaseid = models.ForeignKey(Releases, null=True,
        db_column='pubreleaseid')
    buildtype = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    trovename = models.CharField(max_length=128)
    troveversion = models.CharField(max_length=255)
    troveflavor = models.CharField(max_length=4096)
    trovelastchanged = models.DecimalField(max_digits=14,
        decimal_places=3)
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(rbuildermodels.Users, db_column='createdby',
        related_name='imageCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3,
        null=True)
    updatedby = models.ForeignKey(rbuildermodels.Users, db_column='updatedby',
        related_name='imageUpdater', null=True)
    deleted = models.SmallIntegerField()
    buildcount = models.IntegerField()
    productversionid = models.ForeignKey(Version,
        db_column='productversionid')
    stagename = models.CharField(max_length=255)
    status = models.IntegerField()
    statusmessage = models.TextField()

    def get_absolute_url(self, request, parents=None, model=None):
        if parents:
            if isinstance(parents[0], Project):
                self.view_name = "ProjectImages"
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents, model)

class Downloads(modellib.XObjModel):
    class Meta:
        db_table = u'urldownloads'

    imageId = models.ForeignKey(Image, db_column='urlid')
    timedownloaded = models.CharField(max_length=14)
    ip = models.CharField(max_length=64)
    



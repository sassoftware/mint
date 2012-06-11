#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import urlparse

from django.db import models
from django.conf import settings

from mint.django_rest.rbuilder import modellib

XObjHidden = modellib.XObjHidden

class Fault(modellib.XObjModel):
    class Meta:
        abstract = True
    code = models.IntegerField(null=True)
    message = models.CharField(max_length=8092, null=True)
    traceback = models.TextField(null=True)

class DatabaseVersion(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'databaseversion'
    version = models.SmallIntegerField(null=True)
    minor = models.SmallIntegerField(null=True)

class UserGroups(modellib.XObjModel):
    usergroupid = models.AutoField(primary_key=True)
    usergroup = models.CharField(unique=True, max_length=128)
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'usergroups'
        
    def __unicode__(self):
        return self.usergroup

class Users(modellib.XObjModel):
    userid = models.AutoField(primary_key=True)
    username = models.CharField(unique=True, max_length=128)
    fullname = models.CharField(max_length=128)
    # salt has binary data, django is unhappy about that.
    salt = models.TextField() # This field type is a guess.
    passwd = models.CharField(max_length=254)
    email = models.CharField(max_length=128)
    displayemail = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    timeaccessed = models.DecimalField(max_digits=14, decimal_places=3)
    active = models.SmallIntegerField()
    blurb = models.TextField()
    groups = models.ManyToManyField(UserGroups, through="UserGroupMembers", related_name='groups')
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'users'
        
    def __unicode__(self):
        return self.username
        
class UserGroupMembers(modellib.XObjModel):
    usergroupid = models.ForeignKey(UserGroups, db_column='usergroupid', related_name='group')
    userid = models.ForeignKey(Users, db_column='userid', related_name='usermember')
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'usergroupmembers'
    
class Products(modellib.XObjModel):
    productId = models.AutoField(primary_key=True, db_column='projectid', blank=True)
    hostname = models.CharField(unique=True, max_length=63)
    name = models.CharField(unique=True, max_length=128)
    namespace = models.CharField(max_length=16, null=True)
    domainname = models.CharField(max_length=128)
    shortname = models.CharField(unique=True, max_length=63)
    projecturl = models.CharField(max_length=128, null=True, blank=True)
    repositoryHostName = models.CharField(max_length=255, db_column='fqdn')
    description = models.TextField(null=True, blank=True)
    prodtype = models.CharField(max_length=128)
    commitemail = models.CharField(max_length=128, null=True, blank=True)
    backupexternal = models.SmallIntegerField(null=True, blank=True)
    timecreated = models.DecimalField(max_digits=14, decimal_places=3, blank=True)
    timemodified = models.DecimalField(max_digits=14, decimal_places=3, blank=True)
    hidden = models.SmallIntegerField()
    creatorid = models.ForeignKey(Users, db_column='creatorid', related_name='creator', null=True)
    members = models.ManyToManyField(Users, through="Members", related_name='members')
    
    view_name = 'Projects'
    objects = modellib.ProductsManager()
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'projects'
        
    def __unicode__(self):
        return self.hostname
        
    def _attributes(self):
        return ({'id': self.hostname})

    def get_absolute_url(self, request=None, parents=None, values=None):
        parents = [Pk(self.shortname)]
        return modellib.XObjModel.get_absolute_url(self, request, parents,
            values)

class Members(modellib.XObjModel):
    productId = models.ForeignKey(Products, db_column='projectid', related_name='product')
    userid = models.ForeignKey(Users, db_column='userid', related_name='user')
    level = models.SmallIntegerField()
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'projectusers'
        
class Pk(object):
    def __init__(self, pk):
        self.pk = pk

class Versions(modellib.XObjIdModel):
    productVersionId = models.AutoField(primary_key=True,
        db_column='productversionid')
    productId = models.ForeignKey(Products, db_column='projectid')
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'productversions'
    view_name = 'MajorVersions'

    def __unicode__(self):
        return self.name
        
    def get_absolute_url(self, request=None, parents=None, values=None):
        parents = [Pk(self.productId.shortname), Pk(self.name)]
        return modellib.XObjIdModel.get_absolute_url(self, request, parents,
            values)

    def serialize(self, request=None, values=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request, values)
        xobj_model._xobj.text = self.name
        return xobj_model

class Releases(modellib.XObjModel):
    pubreleaseid = models.AutoField(primary_key=True)
    productId = models.ForeignKey(Products, db_column='projectid', related_name='releasesProduct')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32)
    description = models.TextField()
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(Users, db_column='createdby', related_name='releaseCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3)
    updatedby = models.ForeignKey(Users, db_column='updatedby', related_name='releaseUpdater')
    timepublished = models.DecimalField(max_digits=14, decimal_places=3)
    publishedby = models.ForeignKey(Users, db_column='publishedby', related_name='releasePublisher')
    shouldmirror = models.SmallIntegerField()
    timemirrored = models.DecimalField(max_digits=14, decimal_places=3)
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'publishedreleases'
     
    def __unicode__(self):
        return self.name
               
class Images(modellib.XObjModel):
    imageId = models.AutoField(primary_key=True, db_column='buildid')
    productId = models.ForeignKey(Products, db_column='projectid')
    pubreleaseid = models.ForeignKey(Releases, null=True, db_column='pubreleaseid')
    buildtype = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    trovename = models.CharField(max_length=128)
    troveversion = models.CharField(max_length=255)
    troveflavor = models.CharField(max_length=4096)
    trovelastchanged = models.DecimalField(max_digits=14, decimal_places=3)
    timecreated = models.DecimalField(max_digits=14, decimal_places=3)
    createdby = models.ForeignKey(Users, db_column='createdby', related_name='imageCreator')
    timeupdated = models.DecimalField(max_digits=14, decimal_places=3, null=True)
    updatedby = models.ForeignKey(Users, db_column='updatedby', related_name='imageUpdater', null=True)
    deleted = models.SmallIntegerField()
    buildcount = models.IntegerField()
    productversionid = models.ForeignKey(Versions, db_column='productversionid')
    stagename = models.CharField(max_length=255)
    status = models.IntegerField()
    statusmessage = models.TextField()
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'builds'
        
    def __unicode__(self):
        return self.name
        
class Downloads(modellib.XObjModel):
    imageId = models.ForeignKey(Images, db_column='urlid')
    timedownloaded = models.CharField(max_length=14)
    ip = models.CharField(max_length=64)
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'urldownloads'

class Sessions(modellib.XObjModel):
    sessionId = models.AutoField(primary_key=True, db_column='sessidx')
    sid = models.CharField(max_length=64, unique=True)
    data = models.TextField()
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'sessions'

class Targets(modellib.XObjModel):
    targetid = models.IntegerField(primary_key=True)
    targettype = models.CharField(max_length=255)
    targetname = models.CharField(unique=True, max_length=255)
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targets'

    def get_absolute_url(self, request=None, parents=None, values=None):
        path = '/catalog/clouds/%s/instances/%s' % \
            (self.targettype, self.targetname)
        if request:
            uri = request.build_absolute_uri()
            parts = urlparse.urlparse(uri)
            parts = list(parts)
            parts[2] = path
            parts[4] = ''
            return urlparse.urlunparse(parts)
        else:
            return path

class TargetData(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetdata'
    targetid = models.ForeignKey(Targets, db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()
    # Uhm. django does not support multi-column PKs.

class TargetCredentials(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetcredentials'
    targetcredentialsid = models.AutoField(primary_key=True,
        db_column="targetcredentialsid")
    credentials = models.TextField(null=False, unique=True)

class TargetUserCredentials(modellib.XObjModel):
    targetid = models.ForeignKey(Targets, db_column="targetid")
    userid = models.ForeignKey(Users, db_column="userid")
    targetcredentialsid = models.ForeignKey(TargetCredentials,
        db_column="targetcredentialsid")
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetusercredentials'

class TargetImagesDeployed(modellib.XObjModel):
    targetid = models.ForeignKey(Targets, db_column="targetid")
    fileid = models.IntegerField(null=False)
    targetimageid = models.CharField(max_length=128)
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetimagesdeployed'

class PkiCertificates(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = 'pki_certificates'
        unique_together = [ ('fingerprint', 'ca_serial_index') ]
    fingerprint = models.TextField(primary_key=True)
    purpose = models.TextField(null=False)
    is_ca = models.BooleanField(null=False, default=False)
    x509_pem = models.TextField(null=False)
    pkey_pem = models.TextField(null=False)
    issuer_fingerprint = models.ForeignKey('self',
        db_column="issuer_fingerprint", null=True)
    ca_serial_index = models.IntegerField(null=True)
    time_issued = modellib.DateTimeUtcField(null=False)
    time_expired = modellib.DateTimeUtcField(null=False)

class Jobs(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = 'jobs'
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.TextField(max_length=64, null=False)

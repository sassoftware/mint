#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import urlparse

from django.db import models
from django.conf import settings

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usersmodels

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

# class UserGroups(modellib.XObjModel):
#     usergroupid = models.AutoField(primary_key=True)
#     usergroup = models.CharField(unique=True, max_length=128)
#     
#     class Meta:
#         managed = settings.MANAGE_RBUILDER_MODELS
#         db_table = u'usergroups'
#         
#     def __unicode__(self):
#         return self.usergroup

# class Users(modellib.XObjModel):
#     userid = models.AutoField(primary_key=True)
#     username = models.CharField(unique=True, max_length=128)
#     fullname = models.CharField(max_length=128)
#     # salt has binary data, django is unhappy about that.
#     salt = models.TextField() # This field type is a guess.
#     passwd = models.CharField(max_length=254)
#     email = models.CharField(max_length=128)
#     displayemail = models.TextField()
#     timecreated = models.DecimalField(max_digits=14, decimal_places=3)
#     timeaccessed = models.DecimalField(max_digits=14, decimal_places=3)
#     active = models.SmallIntegerField()
#     blurb = models.TextField()
#     groups = models.ManyToManyField(UserGroups, through="UserGroupMembers", related_name='groups')
#     
#     class Meta:
#         managed = settings.MANAGE_RBUILDER_MODELS
#         db_table = u'users'
#         
#     def __unicode__(self):
#         return self.username
        
# class UserGroupMembers(modellib.XObjModel):
#     usergroupid = models.ForeignKey(UserGroups, db_column='usergroupid', related_name='group')
#     userid = models.ForeignKey(Users, db_column='userid', related_name='usermember')
#     
#     class Meta:
#         managed = settings.MANAGE_RBUILDER_MODELS
#         db_table = u'usergroupmembers'
    
class Products(modellib.XObjModel):

    url_key = ["short_name"]

    product_id = models.AutoField(primary_key=True, db_column='projectid', blank=True)
    host_name = models.CharField(unique=True, max_length=63, db_column='hostname')
    name = models.CharField(unique=True, max_length=128)
    namespace = models.CharField(max_length=16, null=True)
    domain_name = models.CharField(max_length=128, db_column='domainname')
    short_name = models.CharField(unique=True, max_length=63, db_column='shortname')
    project_url = models.CharField(max_length=128, null=True, blank=True, db_column='projecturl')
    repository_host_name = models.CharField(max_length=255, db_column='fqdn')
    description = models.TextField(null=True, blank=True)
    prod_type = models.CharField(max_length=128, db_column='prodtype')
    commit_email = models.CharField(max_length=128, null=True, blank=True, db_column='commitemail')
    backup_external = models.SmallIntegerField(null=True, blank=True, db_column='backupexternal')
    time_created = models.DecimalField(max_digits=14, decimal_places=3, blank=True, db_column='timecreated')
    time_modified = models.DecimalField(max_digits=14, decimal_places=3, blank=True, db_column='timemodified')
    hidden = models.SmallIntegerField()
    creator_id = models.ForeignKey(usersmodels.User, db_column='creatorid', related_name='creator', null=True)
    members = models.ManyToManyField(usersmodels.User, through="Members", related_name='members')
    
    view_name = 'Projects'
    objects = modellib.ProductsManager()
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'projects'
        
    def __unicode__(self):
        return self.hostname
        
    def _attributes(self):
        return ({'id': self.hostname})

class Members(modellib.XObjModel):
    product_id = models.ForeignKey(Products, db_column='projectid', related_name='product')
    user_id = models.ForeignKey(usersmodels.User, db_column='userid', related_name='user')
    level = models.SmallIntegerField()
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'projectusers'
        
class Pk(object):
    def __init__(self, pk):
        self.pk = pk

    def get_url_key(self, *args, **kwargs):
        return self.pk


class Versions(modellib.XObjIdModel):

    url_key = ["product_id", "name"]

    product_version_id = models.AutoField(primary_key=True,
        db_column='productversionid')
    product_id = models.ForeignKey(Products, db_column='projectid')
    namespace = models.CharField(max_length=16)
    name = models.CharField(max_length=16)
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'productversions'
    view_name = 'MajorVersions'

    def __unicode__(self):
        return self.name
        
    def serialize(self, request=None, values=None):
        xobj_model = modellib.XObjIdModel.serialize(self, request)
        xobj_model._xobj.text = self.name
        return xobj_model

class Releases(modellib.XObjModel):
    pub_release_id = models.AutoField(primary_key=True, db_column='pubreleaseid')
    product_id = models.ForeignKey(Products, db_column='projectid', related_name='releasesProduct')
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=32)
    description = models.TextField()
    time_created = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    created_by = models.ForeignKey(usersmodels.User, db_column='createdby', related_name='releaseCreator')
    time_updated = models.DecimalField(max_digits=14, decimal_places=3, db_column='timeupdated')
    updated_by = models.ForeignKey(usersmodels.User, db_column='updatedby', related_name='releaseUpdater')
    time_published = models.DecimalField(max_digits=14, decimal_places=3, db_column='timepublished')
    published_by = models.ForeignKey(usersmodels.User, db_column='publishedby', related_name='releasePublisher')
    should_mirror = models.SmallIntegerField(db_column='shouldmirror')
    time_mirrored = models.DecimalField(max_digits=14, decimal_places=3, db_column='timemirrored')
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'publishedreleases'
     
    def __unicode__(self):
        return self.name
               
class Images(modellib.XObjModel):
    image_id = models.AutoField(primary_key=True, db_column='buildid')
    product_id = models.ForeignKey(Products, db_column='projectid')
    pub_release_id = models.ForeignKey(Releases, null=True, db_column='pubreleaseid')
    build_type = models.IntegerField(db_column='buildtype')
    name = models.CharField(max_length=255)
    description = models.TextField()
    trove_name = models.CharField(max_length=128, db_column='trovename')
    trove_version = models.CharField(max_length=255, db_column='troveversion')
    trove_flavor = models.CharField(max_length=4096, db_column='troveflavor')
    trove_last_changed = models.DecimalField(max_digits=14, decimal_places=3, db_column='trovelastchanged')
    time_created = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    created_by = models.ForeignKey(usersmodels.User, db_column='createdby', related_name='imageCreator')
    time_updated = models.DecimalField(max_digits=14, decimal_places=3, null=True, db_column='timeupdated')
    updated_by = models.ForeignKey(usersmodels.User, db_column='updatedby', related_name='imageUpdater', null=True)
    deleted = models.SmallIntegerField()
    build_count = models.IntegerField(db_column='buildcount')
    product_version_id = models.ForeignKey(Versions, db_column='productversionid')
    stage_name = models.CharField(max_length=255, db_column='stagename')
    status = models.IntegerField()
    status_message = models.TextField(db_column='statusmessage')
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'builds'
        
    def __unicode__(self):
        return self.name
        
class Downloads(modellib.XObjModel):
    image_id = models.ForeignKey(Images, db_column='urlid')
    time_downloaded = models.CharField(max_length=14, db_column='timedownloaded')
    ip = models.CharField(max_length=64)
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'urldownloads'

class Sessions(modellib.XObjModel):
    session_id = models.AutoField(primary_key=True, db_column='sessidx')
    sid = models.CharField(max_length=64, unique=True)
    data = models.TextField()
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'sessions'

class Targets(modellib.XObjModel):
    target_id = models.IntegerField(primary_key=True, db_column='targetid')
    target_type = models.CharField(max_length=255, db_column='targettype')
    target_name = models.CharField(unique=True, max_length=255, db_column='targetname')
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targets'

    def get_absolute_url(self, request=None, parents=None, values=None):
        path = '/catalog/clouds/%s/instances/%s' % \
            (self.target_type, self.target_name)
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
    target_id = models.ForeignKey(Targets, db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()
    # Uhm. django does not support multi-column PKs.

class TargetCredentials(modellib.XObjModel):
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetcredentials'
    target_credentials_id = models.AutoField(primary_key=True,
        db_column="targetcredentialsid")
    credentials = models.TextField(null=False, unique=True)

class TargetUserCredentials(modellib.XObjModel):
    target_id = models.ForeignKey(Targets, db_column="targetid")
    user_id = models.ForeignKey(usersmodels.User, db_column="userid")
    target_credentials_id = models.ForeignKey(TargetCredentials,
        db_column="targetcredentialsid")
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'targetusercredentials'

class TargetImagesDeployed(modellib.XObjModel):
    target_id = models.ForeignKey(Targets, db_column="targetid")
    file_id = models.IntegerField(null=False, db_column='fileid')
    target_image_id = models.CharField(max_length=128, db_column='targetimageid')
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

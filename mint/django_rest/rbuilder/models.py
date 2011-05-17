#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import urlparse

from django.db import models

from xobj import xobj

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
        db_table = u'DatabaseVersion'
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
    
class Pk(object):
    def __init__(self, pk):
        self.pk = pk

class Sessions(modellib.XObjModel):
    session_id = models.AutoField(primary_key=True, db_column='sessidx')
    sid = models.CharField(max_length=64, unique=True)
    data = models.TextField()
    
    class Meta:
        db_table = u'sessions'

class Targets(modellib.XObjModel):
    target_id = models.IntegerField(primary_key=True, db_column='targetid')
    target_type = models.CharField(max_length=255, db_column='targettype')
    target_name = models.CharField(unique=True, max_length=255, db_column='targetname')
    class Meta:
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
        db_table = u'targetdata'
    target_id = models.ForeignKey(Targets, db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()
    # Uhm. django does not support multi-column PKs.

class TargetCredentials(modellib.XObjModel):
    class Meta:
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
        db_table = u'targetusercredentials'

class TargetImagesDeployed(modellib.XObjModel):
    target_id = models.ForeignKey(Targets, db_column="targetid")
    file_id = models.IntegerField(null=False, db_column='fileid')
    target_image_id = models.CharField(max_length=128, db_column='targetimageid')
    class Meta:
        db_table = u'targetimagesdeployed'

class PkiCertificates(modellib.XObjModel):
    class Meta:
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
        db_table = 'jobs'
    job_id = models.AutoField(primary_key=True)
    job_uuid = models.TextField(max_length=64, null=False)

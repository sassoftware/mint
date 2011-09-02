#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import urlparse

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.users import models as usersmodels
from xobj import xobj

XObjHidden = modellib.XObjHidden

class Targets(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='targets')
    list_fields = ['target']

class Target(modellib.XObjModel):
    target_id = models.IntegerField(primary_key=True, db_column='targetid')
    target_type = modellib.ForeignKey('TargetType', db_column='targettype')
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
        
    targetdata_id = models.AutoField(primary_key=True, db_column='targetdataid')    
    target_id = models.ForeignKey(Targets, db_column="targetid")
    name = models.CharField(max_length=255, null=False)
    value = models.TextField()
    # Uhm. django does not support multi-column PKs.

class TargetCredential(modellib.XObjModel):
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

class TargetTypes(modellib.Collection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='target_types')
    list_fields = ['target_type']
    
class TargetType(modellib.XObjModel):
    target_type_id = models.AutoField(primary_key=True, db_column='targettypeid')
    type = models.CharField(max_length=255)
    created_date = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    modified_date = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timeaccessed')
    description = models.TextField(null=True, blank=True)
    
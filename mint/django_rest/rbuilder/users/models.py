#
# Copyright (c) 2011 rPath, Inc.
#
# This program is distributed under the terms of the Common Public License,
# version 1.0. A copy of this license should have been distributed with this
# source file in a file called LICENSE. If it is not present, the license
# is always available at http://www.rpath.com/permanent/licenses/CPL-1.0.
#
# This program is distributed in the hope that it will be useful, but
# without any warranty; without even the implied warranty of merchantability
# or fitness for a particular purpose. See the Common Public License for
# full details.
#
from django.db import models
from mint.django_rest.rbuilder import modellib
from mint.django_rest import settings
from xobj import xobj


class UserGroups(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='user_groups')
    list_fields = ['user_group']


class UserGroup(modellib.XObjIdModel):
    user_group_id = models.AutoField(primary_key=True, db_column='usergroupid')
    user_group = models.CharField(unique=True, max_length=128, db_column='usergroup')

    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'usergroups'

    _xobj = xobj.XObjMetadata(tag='user_group')

    def __unicode__(self):
        return self.user_group


class Users(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='users')
    list_fields = ['user']


class User(modellib.XObjIdModel):
    user_id = models.AutoField(primary_key=True, db_column='userid')
    user_name = models.CharField(unique=True, max_length=128, db_column='username')
    full_name = models.CharField(max_length=128, db_column='fullname')
    # salt has binary data, django is unhappy about that.
    salt = models.TextField() # This field type is a guess.
    passwd = models.CharField(max_length=254)
    email = models.CharField(max_length=128)
    display_email = models.TextField(db_column='displayemail')
    time_created = models.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    time_accessed = models.DecimalField(max_digits=14, decimal_places=3, db_column='timeaccessed')
    active = models.SmallIntegerField()
    blurb = models.TextField()
    groups = models.ManyToManyField(UserGroup, through="UserGroupMembers", related_name='groups')
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'users'
    
    _xobj = xobj.XObjMetadata(tag='user')
        
    def __unicode__(self):
        return self.user_name
        
        
class UserGroupMembers(modellib.XObjModel):
    user_group_id = models.ForeignKey(UserGroup, db_column='usergroupid', related_name='group')
    user_id = models.ForeignKey(User, db_column='userid', related_name='usermember')
    
    class Meta:
        managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'usergroupmembers'
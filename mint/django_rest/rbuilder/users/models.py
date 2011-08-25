#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

from mint.django_rest.rbuilder.users import manager_model

from django.db import connection

class UserGroups(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='user_groups')
    list_fields = ['user_group']


class UserGroup(modellib.XObjIdModel):

    user_group_id = models.AutoField(primary_key=True, db_column='usergroupid')
    name = models.CharField(unique=True, max_length=128, db_column='usergroup')

    class Meta:
        # managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'usergroups'

    _xobj = xobj.XObjMetadata(tag='user_group')
    _xobj_hidden_accessors = set(['user_members_group_id'])


    def __unicode__(self):
        return self.name


class Users(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='users')
    list_fields = ['user']
    view_name = 'Users'

class User(modellib.XObjIdModel):
    objects = manager_model.UserManager()
    user_id = models.AutoField(primary_key=True, db_column='userid')
    user_name = models.CharField(unique=True, max_length=128, db_column='username')
    full_name = models.CharField(max_length=128, db_column='fullname')
    # salt and password should be hidden, users shouldn't see crypted
    # passwords
    salt = modellib.XObjHidden(models.TextField(null=True))
    passwd = modellib.XObjHidden(models.CharField(max_length=254, null=True))
    email = models.CharField(max_length=128)
    display_email = models.TextField(db_column='displayemail')
    created_date = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timecreated')
    modified_date = modellib.DecimalField(max_digits=14, decimal_places=3, db_column='timeaccessed')
    active = modellib.XObjHidden(modellib.APIReadOnly(models.SmallIntegerField()))
    blurb = models.TextField()
    user_groups = modellib.DeferredManyToManyField(UserGroup, through="UserGroupMember", db_column='user_group_id', related_name='group')
    is_admin = modellib.SyntheticField()
    # Field used for the clear-text password when it is to be
    # set/changed
    password = modellib.XObjHidden(modellib.SyntheticField())

    class Meta:
        # managed = settings.MANAGE_RBUILDER_MODELS
        db_table = u'users'

    _xobj = xobj.XObjMetadata(tag='user', attributes = {'id':str})


    _xobj_hidden_accessors = set(['creator', 'package_version_urls_last_modified',
        'packages_last_modified', 'releaseCreator', 'imageCreator', 'package_source_jobs_created',
        'releasePublisher', 'releaseUpdater', 'package_build_jobs_last_modified',
        'package_build_jobs_created', 'package_builds_created', 'package_version_jobs_created',
        'imageUpdater', 'package_version_urls_created', 'package_versions_last_modified',
        'package_source_jobs_last_modified', 'package_builds_last_modified',
        'targetusercredentials_set', 'package_version_jobs_last_modified', 'package_sources_created',
        'system_set', 'package_builds_jobs_last_modified', 'package_sources_last_modified',
        'usermember', 'package_versions_created', 'packages_created', 'user',
        'created_images', 'updated_images', 'project_membership',
        'created_releases', 'updated_releases', 'published_releases', 'user_tags', 
        'tags',
    ])

    def __unicode__(self):
        return self.user_name

    def getIsAdmin(self):
        # A bit of SQL here, so we only do one trip to the db
        cu = connection.cursor()
        cu.execute("""
            SELECT 1
              FROM UserGroupMembers
              JOIN UserGroups USING (usergroupid)
             WHERE UserGroups.usergroup = 'MintAdmin'
               AND UserGroupMembers.userid = %s
        """, [self.user_id])
        row = cu.fetchone()
        return bool(row)

    def set_is_admin(self):
        isAdmin = self.getIsAdmin()
        # Unfortunately we don't have boolean synthetic fields yet, so
        # let's save the string representation of it
        self.is_admin = str(bool(isAdmin)).lower()

    def computeSyntheticFields(self, sender, **kwargs):
        if self.pk is not None:
            self.set_is_admin()

class UserGroupMembers(modellib.Collection):
    class Meta:
        abstract = True
    
    list_fields = ['user_group_member']

    _xobj = xobj.XObjMetadata(tag='user_group_members')


class UserGroupMember(modellib.XObjIdModel):
    
    class Meta:
        db_table = u'usergroupmembers'
        
    user_group_member_id = models.AutoField(primary_key=True, db_column='usergroupmemberid')
    user_group_id = modellib.XObjHidden(modellib.DeferredForeignKey(UserGroup, db_column='usergroupid', related_name='user_members_group_id'))
    user_id = modellib.DeferredForeignKey(User, db_column='userid', related_name='usermember')
    
    _xobj = xobj.XObjMetadata(tag='user_group_member')

class Session(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='session', attributes = {'id':str})
    view_name = 'Session'

    # Blargh. If I add user as a regular field, it won't get serialized,
    # because get_field_dict() won't pick it up. So we cheat here and
    # make user a list.
    list_fields = [ 'user' ]

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

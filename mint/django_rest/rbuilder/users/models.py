#
# Copyright (c) 2011 rPath, Inc.
#

from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

from mint.django_rest.rbuilder.users import manager_model
from mint.django_rest.deco import D
APIReadOnly = modellib.APIReadOnly

class Users(modellib.Collection):
    class Meta:
        abstract = True
        
    _xobj = xobj.XObjMetadata(tag='users')
    list_fields = ['user']
    view_name = 'Users'

class User(modellib.XObjIdModel):

    objects = manager_model.UserManager()
    summary_view = ["user_name", "full_name"]

    user_id = D(models.AutoField(primary_key=True, db_column='userid'), "User id", short="User id")
    user_name = D(models.CharField(unique=True, max_length=128, db_column='username'), "User name, is unique", short="User name")
    full_name = D(models.CharField(max_length=128, db_column='fullname'), "User full name", short="User full name")
    # salt and password should be hidden, users shouldn't see crypted
    # passwords
    salt = modellib.XObjHidden(models.TextField(null=True))
    passwd = modellib.XObjHidden(models.CharField(max_length=254, null=True))
    email = D(models.CharField(max_length=128), "User email", short="User email")
    display_email = D(models.TextField(db_column='displayemail'), "User display email", short="User display email")
    created_date = D(APIReadOnly(modellib.DecimalTimestampField(max_digits=14, decimal_places=3, db_column='timecreated')), "User created date", short="User created date")
    last_login_date = D(APIReadOnly(modellib.DecimalTimestampField(max_digits=14, decimal_places=3, db_column='timeaccessed')), "User last login date", short="User last login date")
    modified_date = D(APIReadOnly(modellib.DecimalTimestampField(max_digits=14, decimal_places=3, db_column='timemodified')), "User modified date", short="User modified date")
    # this is a Django-ism and is not the same as deleted below, Django inactive users are re-activeatable
    # and we largely don't use this
    active = modellib.XObjHidden(modellib.APIReadOnly(models.SmallIntegerField()))
    blurb = models.TextField()
    # code in manager prevents this from being set by non-admins
    is_admin = D(models.BooleanField(default=False, db_column='is_admin'), 'Is user an admin, boolean field, default is "False"')
    external_auth = D(modellib.SyntheticField(models.BooleanField()), "User external auth?", short="User external auth?")

    created_by = D(APIReadOnly(models.ForeignKey('User', related_name='+', db_column='created_by', null=True)), 
        "User created by, is null by default", short="User created by")
    modified_by = D(APIReadOnly(models.ForeignKey('User', related_name='+', db_column='modified_by', null=True)), 
        "User modified by, is null by default", short="User modified by")
    # code in manager prevents this from being set by non-admins
    can_create = D(models.BooleanField(default=True), "User can create resources? Defaults to 'True'", short="User can create?")
    deleted = modellib.XObjHidden(models.BooleanField(default=False))

    # Field used for the clear-text password when it is to be
    # set/changed
    password = modellib.XObjHidden(modellib.SyntheticField())
    roles = modellib.SyntheticField()
    grants = modellib.SyntheticField()

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
        'target_user_credentials', 'package_version_jobs_last_modified', 'package_sources_created',
        'system_set', 'package_builds_jobs_last_modified', 'package_sources_last_modified',
        'usermember', 'package_versions_created', 'packages_created', 'user',
        'created_images', 'updated_images', 'project_membership',
        'created_releases', 'updated_releases', 'published_releases', 'tags', 'user_tags',
        'user_roles', 'jobs', 'auth_tokens',
    ])

    def __unicode__(self):
        return self.user_name

    def _populateExternalAuthField(self):
        """
        Compute external auth field based on whether or not the password
        is set.
        """
        self.external_auth = str(self.passwd is None).lower()

    def computeSyntheticFields(self, sender, **kwargs):
        self._populateExternalAuthField()
        # sub-collections off of user
        self.roles = modellib.HrefFieldFromModel(self, viewName='UserRoles')

class Session(modellib.XObjIdModel):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag='session', attributes = {'id':str})
    view_name = 'Session'
    
    favorite_querysets = modellib.HrefField(href="/api/v1/favorites/query_sets")

    # Blargh. If I add user as a regular field, it won't get serialized,
    # because get_field_dict() won't pick it up. So we cheat here and
    # make user a list.
    list_fields = [ 'user' ]

for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

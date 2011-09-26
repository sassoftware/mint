#
# Copyright (c) 2011 rPath, Inc.
#

from django.db import models
from mint.django_rest.rbuilder import modellib
from xobj import xobj
import sys

from mint.django_rest.rbuilder.users import manager_model
from django.db import connection


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
    _is_admin = modellib.XObjHidden(modellib.APIReadOnly(
        models.BooleanField(default=False, db_column='is_admin')))

    is_admin = modellib.SyntheticField()

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
        'user_roles', 'jobs',
    ])

    def __unicode__(self):
        return self.user_name

    @staticmethod
    def _toBool(val):
        if val is None:
            return None
        if not isinstance(val, basestring):
            val = str(val)
        val = val.lower()
        if val in ('true', 'false'):
            return val == 'true'
        if val == '1':
            return True
        return False

    def setIsAdmin(self, isAdmin):
        """Set private admin flag, to be called after the caller's adminship
        has been verified only.
        """
        self._is_admin = isAdmin

    def getIsAdmin(self):
        return self._toBool(self._is_admin)

    def _populateAdminField(self):
        """Copy private is_admin value to public field."""
        # Unfortunately we don't have boolean synthetic fields yet, so
        # let's save the string representation of it
        if self._is_admin is not None:
            self.is_admin = str(bool(self._is_admin)).lower()

    def computeSyntheticFields(self, sender, **kwargs):
        self._populateAdminField()
        # sub-collections off of user
        self.roles = modellib.HrefField(
           href="/api/v1/users/%s/roles" % self.user_id
        )


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

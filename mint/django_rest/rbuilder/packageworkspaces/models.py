#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import sys
from django.db import models
from mint.django_rest.deco import D
from mint.django_rest.rbuilder import modellib
from xobj import xobj

from mint.django_rest.rbuilder.inventory import models as inventorymodels

class PackageWorkspaces(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_workspaces')
    list_fields = ['package_workspace']
    

class PackageWorkspace(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'packageworkspaces_package_workspace'
    _xobj = xobj.XObjMetadata(
                tag = 'package_workspace')

    
    package_workspace_id = D(models.AutoField(primary_key=True), 
        "Database id of package workspace")
    name = D(models.CharField(max_length=100, unique=True),
        "Name of package workspace")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package workspace was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package workspace was last modified (UTC)")

    load_fields = [name]

class PackageSessions(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_sessions')
    list_fields = ['package_session']


class PackageSession(modellib.XObjIdModel):

    class Meta:
        db_table = "packageworkspaces_package_session"
    _xobj = xobj.XObjMetadata(tag="package_session")

    package_session_id = D(models.AutoField(primary_key=True), 
        "Database id of package session")
    package_workspace = D(modellib.ForeignKey(PackageWorkspace,
        related_name="package_sessions"),
        "Package workspace for this package session")

    def get_absolute_url(self, request, *args, **kwargs):
        return modellib.XObjIdModel.get_absolute_url(self, request,
            parents=[self.package_workspace, self])


class PackageSessionJob(modellib.XObjIdModel):

    class Meta:
        db_table = "packageworkspaces_package_session_job"
    _xobj = xobj.XObjMetadata(tag="job")

    package_session_job_id = D(models.AutoField(primary_key=True), 
        "Database id of package session job")
    package_session = D(modellib.ForeignKey(PackageSession,
        related_name="package_session_jobs"),
        "Package Session")
    job = D(modellib.DeferredForeignKey(inventorymodels.Job, unique=True,
        related_name="package_sessions"),
        "Job")


class PackageSessionAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packageworkspaces_package_session_action"
    _xobj = xobj.XObjMetadata(tag="action")

    COMMIT = "commit"
    COMMIT_DESC = "commit the package session"
    BUILD = "build"
    BUILD_DESC = "build the package session"

    ACTION_CHOICES = (
        (COMMIT, COMMIT_DESC),
        (BUILD, BUILD_DESC),
    )

    package_session_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package session action")
    name = D(models.TextField(choices=ACTION_CHOICES),
        "name")
    description = D(models.TextField(),
        "description")


class PackageSessionUrl(modellib.XObjIdModel):

    class Meta:
        db_table = "packageworkspaces_package_session_url"
    _xobj = xobj.XObjMetadata(tag="package_session_url")
    
    package_session_url_id = D(models.AutoField(primary_key=True),
        "Database id of package session url")
    package_session = D(modellib.ForeignKey(PackageSession,
        related_name="package_session_urls"),
        "Package session for this url")
    url = D(models.TextField(),
        "The url")
    file_path = D(models.TextField(null=True),
        "Path on the file system of the downloaded url")
    downloaded_date = D(modellib.DateTimeUtcField(null=True),
        "Downloaded date of the file")
    file_size = D(models.IntegerField(null=True), 
        "Size of file in KB")


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

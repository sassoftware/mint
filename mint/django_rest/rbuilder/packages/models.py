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

from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models as inventorymodels

class Packages(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='packages')
    list_fields = ['package']


class Package(modellib.XObjIdModel):
    
    class Meta:
        db_table = 'packages_package'
    _xobj = xobj.XObjMetadata(tag='package')
    
    package_id = D(models.AutoField(primary_key=True), 
        "Database id of package")
    name = D(models.CharField(max_length=100, unique=True),
        "Name of package")
    description = D(models.TextField(),
        "Description of package")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="packages_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="packages_last_modified"),
        "the user that last modified the resource")


class PackageVersions(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_versions')
    list_fields = ['package_version']


class AllPackageVersions(PackageVersions):

    class Meta:
        abstract = True


class PackageVersion(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_version"
    _xobj = xobj.XObjMetadata(tag="package_version")

    package_version_id = D(models.AutoField(primary_key=True), 
        "Database id of package version")
    package = D(modellib.DeferredForeignKey(Package,
        related_name="package_versions", view_name="PackageVersions",
        ref_name="id"),
        "Package for this package version")
    name = D(models.TextField(),
        "Version")
    license = D(models.TextField(),
        "License")
    consumable = D(models.BooleanField(),
        "Consumable")
    actions = D(modellib.ManyToManyField("PackageActionType",
        through="PackageVersionAction"),
        "Package version actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_versions_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_versions_last_modified"),
        "the user that last modified the resource")
    committed = D(models.BooleanField(default=False),
        "if the package version has been committed.")


class PackageVersionAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_version_actions"
    _xobj = xobj.XObjMetadata(tag="package_version_action")

    package_version_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package version action")
    package_version = D(modellib.ForeignKey(PackageVersion,
        related_name="package_version_actions"),
        "Package Version")
    package_action_type = D(modellib.ForeignKey("PackageActionType"),
        "Package action type")
    visible = D(models.BooleanField(),
        "If the action is visible")
    enabled = D(models.BooleanField(),
        "If the action is enabled")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version action was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version action was last modified (UTC)")


class PackageVersionJobs(modellib.XObjIdModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag="package_version_jobs")
    list_fields = ["package_version_job"]

class PackageVersionJob(modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_version_job"
    _xobj = xobj.XObjMetadata(tag="package_version_job")

    url_key = ["package_version.package", "package_version", "pk"]

    package_version_job_id = D(models.AutoField(primary_key=True),
        "Database id of package version job")
    package_version = D(modellib.DeferredForeignKey(PackageVersion,
        related_name="package_version_jobs", view_name="PackageVersionJobs",
        ref_name="id"),
        "Package version")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_version_jobs"),
        "Package action type")
    job = D(modellib.ForeignKey(inventorymodels.Job),
        "Job")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_version_jobs_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_version_jobs_last_modified"),
        "the user that last modified the resource")


class PackageVersionUrl(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_version_url"
    _xobj = xobj.XObjMetadata(tag="package_version_url")
    
    package_version_url_id = D(models.AutoField(primary_key=True),
        "Database id of package version url")
    package_version = D(modellib.ForeignKey(PackageVersion,
        related_name="package_version_urls"),
        "Package version for this url")
    url = D(models.TextField(),
        "The url")
    file_path = D(models.TextField(null=True),
        "Path on the file system of the downloaded url")
    downloaded_date = D(modellib.DateTimeUtcField(null=True),
        "Downloaded date of the file")
    file_size = D(models.IntegerField(null=True), 
        "Size of file in KB")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version url was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version url was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_version_urls_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_version_urls_last_modified"),
        "the user that last modified the resource")


class PackageSources(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_sources')
    list_fields = ['package_source']

class PackageSource(modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_source"
    _xobj = xobj.XObjMetadata(tag="package_source")
    _xobj_hidden_accessors = set(["package_source_actions"])

    url_key = ["package_version", "pk"]

    package_source_id = D(models.AutoField(primary_key=True), 
        "Database id of package source")
    package_version = D(modellib.DeferredForeignKey(PackageVersion,
        related_name="package_sources", view_name="PackageSources",
        ref_name="id"),
        "Package version")
    actions = D(modellib.ManyToManyField("PackageActionType",
        through="PackageSourceAction"),
        "Package source actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package source was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package source was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_sources_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_sources_last_modified"),
        "the user that last modified the resource")
    built = D(models.BooleanField(default=False),
        "if the package source has been built")
    trove = D(modellib.ForeignKey(inventorymodels.Trove, null=True),
        "committed source trove")


class PackageSourceAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_source_actions"
    _xobj = xobj.XObjMetadata(tag="package_source_action")

    package_source_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package source action")
    package_source = D(modellib.ForeignKey(PackageSource,
        related_name="package_source_actions"),
        "Package Source")
    package_action_type = D(modellib.ForeignKey("PackageActionType"),
        "Package action type")
    enabled = D(models.BooleanField(),
        "If the action is enabled")
    visible = D(modellib.SyntheticField(),
        "If the action is visible")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package source action was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package source action was last modified (UTC)")


class PackageSourceJobs(modellib.XObjIdModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag="package_source_jobs")
    list_fields = ["package_source_job"]


class PackageSourceJob(modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_source_job"
    _xobj = xobj.XObjMetadata(tag="package_source_job")

    url_key = ["package_source", "pk"]

    package_source_job_id = D(models.AutoField(primary_key=True),
        "Database id of package source job")
    package_source = D(modellib.DeferredForeignKey(PackageSource,
        related_name="package_source_jobs", view_name="PackageSourceJobs",
        ref_name="id"),
        "Package source")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_source_jobs"),
        "Package action type")
    job = D(modellib.ForeignKey(inventorymodels.Job),
        "Job")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package source job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package source job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_source_jobs_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_source_jobs_last_modified"),
        "the user that last modified the resource")


class PackageBuilds(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_builds')
    list_fields = ['package_build']


class PackageBuild(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_build"
    _xobj = xobj.XObjMetadata(tag="package_build")
    _xobj_hidden_accessors = set(["package_build_actions"])

    url_key = ["package_source", "pk"]

    package_build_id = D(models.AutoField(primary_key=True), 
        "Database id of package build")
    package_source = D(modellib.DeferredForeignKey(PackageSource,
        related_name="package_builds", view_name="PackageBuilds",
        ref_name="id"),
        "Package Source")
    actions = D(modellib.ManyToManyField("PackageActionType",
        through="PackageBuildAction"),
        "Package build actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package build was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package build was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_builds_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_builds_last_modified"),
        "the user that last modified the resource")
    troves = D(modellib.ManyToManyField(inventorymodels.Trove),
        "built binary troves")


class PackageBuildAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_build_actions"
    _xobj = xobj.XObjMetadata(tag="package_build_action")

    package_build_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package build action")
    package_build = D(modellib.ForeignKey(PackageBuild,
        related_name="package_build_actions"),
        "Package Build")
    package_action_type = D(modellib.ForeignKey("PackageActionType"),
        "Package action type")
    visible = D(models.BooleanField(),
        "If the action is visible")
    enabled = D(models.BooleanField(),
        "If the action is enabled")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package build action was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package build action was last modified (UTC)")


class PackageBuildJobs(modellib.XObjIdModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag="package_build_jobs")
    list_fields = ["package_build_job"]


class PackageBuildJob(modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_build_job"
    _xobj = xobj.XObjMetadata(tag="package_build_job")

    url_key = ["package_build", "pk"]

    package_build_job_id = D(models.AutoField(primary_key=True),
        "Database id of package build job")
    package_build = D(modellib.DeferredForeignKey(PackageBuild,
        related_name="package_build_jobs", view_name="PackageBuildJobs",
        ref_name="id"),
        "Package build")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_build_jobs"),
        "Package action type")
    job = D(modellib.ForeignKey(inventorymodels.Job),
        "Job")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package build job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package build job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_build_jobs_created"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(rbuildermodels.Users, null=True,
        related_name="package_builds_jobs_last_modified"),
        "the user that last modified the resource")


class PackageActionType(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_action_type"
    _xobj = xobj.XObjMetadata(tag="package_action_type")

    COMMIT = "commit"
    COMMIT_DESC = "commit the package version"
    BUILD = "build"
    BUILD_DESC = "build the package version"
    PROMOTE_VERSION = "promote_version"
    PROMOTE_VERSION_DESC = "promote the package version"
    PROMOTE = "promote"
    PROMOTE_DESC = "promote the package"

    ACTION_CHOICES = (
        (COMMIT, COMMIT_DESC),
        (BUILD, BUILD_DESC),
        (PROMOTE_VERSION, PROMOTE_VERSION_DESC),
        (PROMOTE, PROMOTE_DESC),
    )

    package_action_type_id = D(models.AutoField(primary_key=True), 
        "Database id of package session action")
    name = D(models.TextField(choices=ACTION_CHOICES),
        "name")
    description = D(models.TextField(),
        "description")
    descriptor = D(models.TextField(),
        "descriptor")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package action type was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package action type was last modified (UTC)")


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

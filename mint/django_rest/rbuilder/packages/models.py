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

# from mint.django_rest.rbuilder import models as rbuildermodels
from mint.django_rest.rbuilder.inventory import models as inventorymodels
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.django_rest.rbuilder.jobs import models as jobmodels
from mint.lib import data as mintdata

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
    name = D(models.TextField(unique=True),
        "Name of package")
    description = D(models.TextField(null=True),
        "Description of package")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="packages_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="packages_last_modified", text_field="user_name"),
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
    _xobj_hidden_m2m = set(["possible_actions"])

    package_version_id = D(models.AutoField(primary_key=True), 
        "Database id of package version")
    package = D(modellib.DeferredForeignKey(Package,
        related_name="package_versions", view_name="PackageVersions"),
        "Package for this package version")
    name = D(models.TextField(),
        "Version")
    description = D(models.TextField(null=True),
        "Description")
    license = D(models.TextField(null=True),
        "License")
    consumable = D(models.BooleanField(),
        "Consumable")
    possible_actions = D(models.ManyToManyField("PackageActionType",
        through="PackageVersionAction"),
        "Package version actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_versions_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_versions_last_modified", text_field="user_name"),
        "the user that last modified the resource")
    committed = D(models.BooleanField(default=False),
        "if the package version has been committed.")
    package_name = D(modellib.SyntheticField(),
        "name of the associated package")

    def serialize(self, *args, **kwargs):
        xobjModel = modellib.XObjIdModel.serialize(self, *args, **kwargs)
        xobjModel.package_name = self.package.name
        return xobjModel


class PackageVersionAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_version_action"
    _xobj = xobj.XObjMetadata(tag="package_version_action")

    url_key = ["package_version", "pk"]

    package_version_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package version action")
    package_version = D(modellib.ForeignKey(PackageVersion,
        related_name="actions"),
        "Package Version")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_version_actions", text_field="description"),
        "Package action type")
    visible = D(models.BooleanField(default=True),
        "If the action is visible")
    enabled = D(models.BooleanField(default=False),
        "If the action is enabled")
    descriptor = D(models.TextField(null=True),
        "descriptor")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version action was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version action was last modified (UTC)")


class JobData(modellib.XObjModel):
    
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag="job_data")

class PackageVersionJobs(modellib.XObjIdModel):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(tag="package_version_jobs")
    list_fields = ["package_version_job"]

class PackageJobSerializerMixin(object):
    def serialize(self, *args, **kwargs):
        xobjModel = modellib.XObjIdModel.serialize(self, *args, **kwargs)
        if self.job_data:
            unMarshalledJobData = mintdata.unmarshalGenericData(self.job_data)
            xobjModel.job_data = JobData()
            for k, v in unMarshalledJobData.items():
                setattr(xobjModel.job_data, k, v)
        return xobjModel

class PackageVersionJob(PackageJobSerializerMixin, modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_version_job"
    _xobj = xobj.XObjMetadata(tag="package_version_job")

    url_key = ["package_version.package", "package_version", "pk"]

    objects = modellib.PackageJobManager()

    package_version_job_id = D(models.AutoField(primary_key=True),
        "Database id of package version job")
    package_version = D(modellib.DeferredForeignKey(PackageVersion,
        related_name="jobs", view_name="PackageVersionJobs"),
        "Package version")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_version_jobs", text_field="description"),
        "Package action type")
    job = D(modellib.ForeignKey(jobmodels.Job, null=True,
        related_name="package_version_jobs"),
        "Job")
    job_data = D(models.TextField(null=True),
        "Job data")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package version job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package version job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_version_jobs_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_version_jobs_last_modified",
        text_field="user_name"),
        "the user that last modified the resource")

class PackageVersionUrls(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_version_urls')
    list_fields = ['package_version_url']

class PackageVersionUrl(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_version_url"
    _xobj = xobj.XObjMetadata(tag="package_version_url")
    
    url_key = ["package_version", "pk"]

    package_version_url_id = D(models.AutoField(primary_key=True),
        "Database id of package version url")
    package_version = D(modellib.DeferredForeignKey(PackageVersion,
        related_name="package_version_urls", view_name="PackageVersionUrls"),
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
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_version_urls_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_version_urls_last_modified", text_field="user_name"),
        "the user that last modified the resource")

    load_fields = [url]

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
    _xobj_hidden_m2m = set(["possible_actions"])

    url_key = ["package_version", "pk"]

    package_source_id = D(models.AutoField(primary_key=True), 
        "Database id of package source")
    package_version = D(modellib.DeferredForeignKey(PackageVersion,
        related_name="package_sources", view_name="PackageSources"),
        "Package version")
    possible_actions = D(models.ManyToManyField("PackageActionType",
        through="PackageSourceAction"),
        "Package source actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package source was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package source was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_sources_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_sources_last_modified", text_field="user_name"),
        "the user that last modified the resource")
    built = D(models.BooleanField(default=False),
        "if the package source has been built")
    trove = D(modellib.ForeignKey(inventorymodels.Trove, null=True,
        related_name="package_sources"),
        "committed source trove")


class PackageSourceAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_source_action"
    _xobj = xobj.XObjMetadata(tag="package_source_action")

    package_source_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package source action")
    package_source = D(modellib.ForeignKey(PackageSource,
        related_name="actions"),
        "Package Source")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_source_actions", text_field="description"),
        "Package action type")
    enabled = D(models.BooleanField(),
        "If the action is enabled")
    visible = D(models.BooleanField(),
        "If the action is visible")
    descriptor = D(models.TextField(null=True),
        "descriptor")
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


class PackageSourceJob(PackageJobSerializerMixin, modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_source_job"
    _xobj = xobj.XObjMetadata(tag="package_source_job")

    url_key = ["package_source", "pk"]

    objects = modellib.PackageJobManager()

    package_source_job_id = D(models.AutoField(primary_key=True),
        "Database id of package source job")
    package_source = D(modellib.DeferredForeignKey(PackageSource,
        related_name="jobs", view_name="PackageSourceJobs"),
        "Package source")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_source_jobs", text_field="description"),
        "Package action type")
    job = D(modellib.ForeignKey(jobmodels.Job, null=True,
        related_name="package_source_jobs"),
        "Job")
    job_data = D(models.TextField(null=True),
        "Job data")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package source job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package source job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_source_jobs_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_source_jobs_last_modified",
        text_field="user_name"),
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
    _xobj_hidden_m2m = set(["possible_actions"])

    url_key = ["package_source", "pk"]

    package_build_id = D(models.AutoField(primary_key=True), 
        "Database id of package build")
    package_source = D(modellib.DeferredForeignKey(PackageSource,
        related_name="package_builds", view_name="PackageBuilds"),
        "Package Source")
    possible_actions = D(models.ManyToManyField("PackageActionType",
        through="PackageBuildAction"),
        "Package build actions")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package build was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package build was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_builds_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_builds_last_modified", text_field="user_name"),
        "the user that last modified the resource")
    troves = D(models.ManyToManyField(inventorymodels.Trove),
        "built binary troves")


class PackageBuildAction(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_build_action"
    _xobj = xobj.XObjMetadata(tag="package_build_action")

    package_build_action_id = D(models.AutoField(primary_key=True), 
        "Database id of package build action")
    package_build = D(modellib.ForeignKey(PackageBuild,
        related_name="actions"),
        "Package Build")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_build_actions", text_field="description"),
        "Package action type")
    visible = D(models.BooleanField(),
        "If the action is visible")
    enabled = D(models.BooleanField(),
        "If the action is enabled")
    descriptor = D(models.TextField(null=True),
        "descriptor")
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


class PackageBuildJob(PackageJobSerializerMixin, modellib.XObjIdModel):
    
    class Meta:
        db_table = "packages_package_build_job"
    _xobj = xobj.XObjMetadata(tag="package_build_job")

    url_key = ["package_build", "pk"]

    objects = modellib.PackageJobManager()

    package_build_job_id = D(models.AutoField(primary_key=True),
        "Database id of package build job")
    package_build = D(modellib.DeferredForeignKey(PackageBuild,
        related_name="jobs", view_name="PackageBuildJobs"),
        "Package build")
    package_action_type = D(modellib.ForeignKey("PackageActionType",
        related_name="package_build_jobs", text_field="description"),
        "Package action type")
    job = D(modellib.ForeignKey(jobmodels.Job, null=True,
        related_name="package_build_jobs"),
        "Job")
    job_data = D(models.TextField(null=True),
        "Job data")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package build job was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package build job was last modified (UTC)")
    created_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_build_jobs_created", text_field="user_name"),
        "the user that created the resource")
    modified_by = D(modellib.ForeignKey(usersmodels.User, null=True,
        related_name="package_builds_jobs_last_modified",
        text_field="user_name"),
        "the user that last modified the resource")


class PackageActionTypes(modellib.Collection):

    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag='package_action_types')
    list_fields = ['package_action_type']

class PackageActionType(modellib.XObjIdModel):

    class Meta:
        db_table = "packages_package_action_type"
    _xobj = xobj.XObjMetadata(tag="package_action_type")
    _xobj_hidden_accessors = set(["package_version_actions",
        "package_source_actions", "package_build_actions",
        "package_version_jobs", "package_source_jobs",
        "package_build_jobs"])

    DOWNLOAD = "download"
    DOWNLOAD_DESC = "Download package files"
    COMMIT = "commit"
    COMMIT_DESC = "Commit package version"
    BUILD = "build"
    BUILD_DESC = "Build package source"
    PROMOTE_VERSION = "promote_version"
    PROMOTE_VERSION_DESC = "Promote package build"
    PROMOTE = "promote"
    PROMOTE_DESC = "promote the package"
    ANALYZE = "analyze"
    ANALYZE_DESC = "analyze package files"

    ACTION_CHOICES = (
        (DOWNLOAD, DOWNLOAD_DESC),
        (COMMIT, COMMIT_DESC),
        (BUILD, BUILD_DESC),
        (PROMOTE_VERSION, PROMOTE_VERSION_DESC),
        (PROMOTE, PROMOTE_DESC),
        (ANALYZE, ANALYZE_DESC),
    )

    package_action_type_id = D(models.AutoField(primary_key=True), 
        "Database id of package session action")
    name = D(models.TextField(choices=ACTION_CHOICES),
        "name")
    description = D(models.TextField(),
        "description")
    created_date = D(modellib.DateTimeUtcField(auto_now_add=True),
        "the date the package action type was created (UTC)")
    modified_date = D(modellib.DateTimeUtcField(auto_now_add=True,
        auto_now=True),
        "the date the package action type was last modified (UTC)")


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj

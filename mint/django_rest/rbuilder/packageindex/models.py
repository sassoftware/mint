#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from conary import versions

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.projects.models import Project
from mint.django_rest.deco import D
from xobj import xobj


class Packages(modellib.Collection):
    class Meta:
        abstract = True
    _xobj = xobj.XObjMetadata(
                tag = "packages")
    list_fields = ["package"]
    package = []

class Package(modellib.XObjIdModel):
    _xobj = xobj.XObjMetadata(
                tag='package')

    class Meta:
        db_table = "packageindex"

    package_id = D(models.AutoField(primary_key=True, db_column='pkgid'), 'The package ID')
    project = D(modellib.ForeignKey(Project,
        db_column="projectid"), 'Project attached to a package')
    name = D(models.TextField(), 'Package name')
    version = D(models.TextField(), 'Package version')
    server_name = D(models.TextField(db_column="servername"), 'Name of the associated server')
    branch_name = D(models.TextField(db_column="branchname"), 'Project branch name')
    is_source = D(models.IntegerField(db_column="issource", default=0), 'Is an integer, defaults to 0')
    trailing_label = modellib.SyntheticField()
    trailing_version = modellib.SyntheticField()

    def computeSyntheticFields(self, sender, **kwargs):
        ver = versions.VersionFromString(self.version)
        self.trailing_label = ver.trailingLabel().asString()
        self.trailing_version = ver.trailingRevision().asString()

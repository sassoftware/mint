#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from conary import versions

from django.db import models

from mint.django_rest.rbuilder import modellib
from mint.django_rest.rbuilder.projects.models import Project

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

    package_id = models.AutoField(primary_key=True, db_column='pkgid')
    project = modellib.ForeignKey(Project,
        db_column="projectid")
    name = models.TextField()
    version = models.TextField()
    server_name = models.TextField(db_column="servername")
    branch_name = models.TextField(db_column="branchname")
    is_source = models.IntegerField(db_column="issource", default=0)

    def serialize(self, *args, **kwargs):
        xobjModel = modellib.XObjIdModel.serialize(self, *args, **kwargs)
        trailingLabel = \
            versions.VersionFromString(self.version).trailingLabel().asString()
        xobjModel.trailing_label = trailingLabel
        return xobjModel 
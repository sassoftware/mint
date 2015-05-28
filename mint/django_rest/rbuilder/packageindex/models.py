#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import sys

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
    synthetic_fields = ['trailing_label', 'trailing_version']
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
        if self.version:
            ver = versions.VersionFromString(self.version)
            self.trailing_label = ver.trailingLabel().asString()
            self.trailing_version = ver.trailingRevision().asString()
        else:
            self.trailing_label = self.trailing_version = None


for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, '_xobj'):
        if mod_obj._xobj.tag:
            modellib.type_map[mod_obj._xobj.tag] = mod_obj
    if hasattr(mod_obj, '_meta'):
        modellib.type_map[mod_obj._meta.verbose_name] = mod_obj

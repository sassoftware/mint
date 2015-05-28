#!/usr/bin/python
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


from mint import jobstatus
from mint.rest.modellib import Model
from mint.rest.modellib import fields

class ProductVersion(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    versionId = fields.IntegerField()
    hostname = fields.CharField()
    name = fields.CharField()
    productUrl = fields.UrlField('products', ('hostname',))
    namespace = fields.CharField(displayName='nameSpace')
    description = fields.CharField()
    platformLabel = fields.CharField()
    timeCreated = fields.DateTimeField(editable=False)
    label = fields.CharField()
    platform = fields.UrlField('products.versions.platform', 
                                ('hostname', 'name'))
    platformVersion = fields.UrlField('products.versions.platformVersion', 
                                ('hostname', 'name'))
    stages = fields.UrlField('products.versions.stages', ('hostname', 'name'))
    definition = fields.UrlField('products.versions.definition', 
                                 ('hostname', 'name'))
    imageTypeDefinitions = fields.UrlField(
                              'products.versions.imageTypeDefinitions',
                              ('hostname', 'name'))
    imageDefinitions = fields.UrlField(
                              'products.versions.imageDefinitions',
                              ('hostname', 'name'))
    images = fields.UrlField('products.versions.images',
                              ('hostname', 'name'))
    sourceGroup = fields.CharField()

    def get_absolute_url(self):
        return 'products.versions', self.hostname, self.name

    def __repr__(self):
        return 'models.ProductVersion(%r, %r, %r)' % (self.versionId, self.hostname, self.name)

class ProductVersionList(Model):
    class Meta(object):
        name = 'productVersions'

    versions = fields.ListField(ProductVersion, displayName='productVersion')
    def addProductVersion(self, *args, **kwargs):
        self.versions.append(ProductVersion(*args, **kwargs))


class Stage(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    hostname = fields.CharField()
    version = fields.CharField()
    name  = fields.CharField()
    label = fields.CharField()
    isPromotable = fields.BooleanField()
    groups = fields.UrlField('products.repos.search', 
                             ['hostname'], query='type=group&label=%(label)s')
    images = fields.UrlField('products.versions.stages.images',
                             ['hostname', 'version', 'name'])
                            

    def get_absolute_url(self):
        return 'products.versions.stages', self.hostname, self.version, self.name

class Stages(Model):
    stages = fields.ListField(Stage, displayName='stage')

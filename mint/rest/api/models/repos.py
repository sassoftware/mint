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


from mint.rest.modellib import Model
from mint.rest.modellib import fields

class TroveFile(Model):
    hostname         = fields.CharField()
    path             = fields.CharField()
    fileVersion      = fields.VersionField()
    pathId           = fields.CharField()
    pathHash         = fields.CharField()
    fileId           = fields.CharField()
    isConfig         = fields.BooleanField()
    isInitialContents = fields.BooleanField()
    isSource          = fields.BooleanField()
    isAutoSource      = fields.BooleanField()
    isTransient      = fields.BooleanField()
    size             = fields.CharField()
    permissions      = fields.CharField()
    owner            = fields.CharField()
    group            = fields.CharField()
    mtime            = fields.CharField()
    target           = fields.CharField()
    provides         = fields.CharField()
    requires         = fields.CharField()
    flavor           = fields.FlavorField()
    tags             = fields.CharField()
    sha1             = fields.CharField()
    trove            = fields.UrlField('products.repos.items', 
                                       ['hostname', 'trove'])
    contents         = fields.UrlField('products.repos.items.files.contents', 
                                       ['hostname', 'trove', 'pathHash'])
    id               = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('products.repos.items.files', self.hostname, self.trove, 
                self.pathHash)

class Trove(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)
    hostname         = fields.CharField()
    name             = fields.CharField()
    version          = fields.VersionField()
    label            = fields.LabelField()
    trailingVersion  = fields.CharField()
    flavor           = fields.FlavorField()
    timeStamp        = fields.CharField()
    images           = fields.UrlField('products.repos.items.images',
                                      ['hostname', 'nvf'])
    files            = fields.ListField(TroveFile, displayName='file')
    imageCount       = fields.IntegerField()
    configuration_descriptor = fields.CharField()

    def getNVF(self):
        return '%s=%s[%s]' % (self.name, self.version, self.flavor)
    nvf = property(getNVF)

    def get_absolute_url(self):
        return ('products.repos.items', self.hostname, 
                 '%s=%s[%s]' % (self.name, self.version, self.flavor))

class TroveList(Model):
    class Meta(object):
        name = 'troves'
    troves   = fields.ListField(Trove, displayName='trove')

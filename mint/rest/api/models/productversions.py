#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
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

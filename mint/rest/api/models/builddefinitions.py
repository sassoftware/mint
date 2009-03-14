#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import Model
from mint.rest.modellib import fields

class IdField(fields.AbsoluteUrlField):
    pass

class _DisplayField(Model):
    href = IdField('aaa', None, isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return 'products.versions', "a", "b"

class Architecture(_DisplayField):
    href = IdField('aaa', None, isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "definition", "architectures", self.href)

class FlavorSet(_DisplayField):
    href = IdField('aaa', None, isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "definition", "flavorSets", self.href)

class ContainerFormat(_DisplayField):
    href = IdField('aaa', None, isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "definition", "containers", self.href)

class BuildDefinition(Model):
    id = IdField('aaa', None, isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()
    container = fields.ModelField(ContainerFormat)
    architecture = fields.ModelField(Architecture)
    flavorSet = fields.ModelField(FlavorSet)

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            self.id)

class BuildDefinitions(Model):
    class Meta(object):
        name = "image-definitions"
    buildDefinitions = fields.ListField(BuildDefinition, displayName = 'image-definition')


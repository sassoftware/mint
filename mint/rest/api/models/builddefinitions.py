#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import Model, ModelMeta
from mint.rest.modellib import fields

from rpath_proddef import imageTypes

class _DisplayField(Model):
    "Base field class"
    hostname = fields.CharField(display=False)
    version = fields.CharField(display=False)
    stageName = fields.CharField(display=False)
    platform = fields.CharField(display=False)

class Architecture(_DisplayField):
    id = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
                'architectures', self.id)

class FlavorSet(_DisplayField):
    id = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
                'flavorSets', self.id)

class ImageModelMeta(ModelMeta):
    # This is a bit twisted - we're copying the class definition from
    # proddef's imageType.Image
    _fieldTypeMap = {
        str: fields.CharField,
        bool: fields.BooleanField,
        int: fields.IntegerField,
    }
    def __new__(mcs, name, bases, attrs):
        for fieldName, fieldType in sorted(imageTypes.Image._attributes.items()):
            attrs[fieldName] = mcs._fieldTypeMap[fieldType](isAttribute = True)
        return ModelMeta.__new__(mcs, name, bases, attrs)

class ImageParams(Model):
    __metaclass__ = ImageModelMeta

class ContainerFormat(_DisplayField):
    id = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()
    options = fields.ModelField(ImageParams)

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
                'containers', self.id)

class StageHref(_DisplayField):
    href = fields.AbsoluteUrlField(isAttribute = True)
    def get_absolute_url(self):
        return ('products.versions.stages', self.hostname, self.version,
            self.href)

class BuildDefinition(_DisplayField):
    id = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()
    imageGroup = fields.CharField()
    sourceGroup = fields.CharField()
    image = fields.ModelField(ImageParams)
    stages = fields.ListField(StageHref, displayName = 'stage')
    container = fields.ModelField(ContainerFormat)
    architecture = fields.ModelField(Architecture)
    flavorSet = fields.ModelField(FlavorSet)

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            'imageDefinitions', self.id)

class BuildDefinitions(Model):
    class Meta(object):
        name = "imageDefinitions"
    buildDefinitions = fields.ListField(BuildDefinition, displayName = 'imageDefinition')

class BuildTemplate(_DisplayField):
    id = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()
    container = fields.ModelField(ContainerFormat)
    architecture = fields.ModelField(Architecture)
    flavorSet = fields.ModelField(FlavorSet)

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            'imageTypeDefinitions', self.id)


class BuildTemplates(Model):
    class Meta(object):
        name = 'imageTypeDefinitions'
    buildTemplates = fields.ListField(BuildTemplate,
        displayName = 'imageTypeDefinition')

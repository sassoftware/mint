#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.modellib import Model, ModelMeta
from mint.rest.modellib import fields

from rpath_common.proddef import imageTypes

class _DisplayField(Model):
    href = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return 'products.versions', "a", "b"

class Architecture(_DisplayField):
    href = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "architectures", self.href)

class FlavorSet(_DisplayField):
    href = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "flavorSets", self.href)

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
            fieldType = fieldType[0]
            attrs[fieldName] = mcs._fieldTypeMap[fieldType](isAttribute = True)
        return ModelMeta.__new__(mcs, name, bases, attrs)

class ImageParams(Model):
    __metaclass__ = ImageModelMeta

class ContainerFormat(_DisplayField):
    href = fields.AbsoluteUrlField(isAttribute = True)
    name = fields.CharField()
    displayName = fields.CharField()
    options = fields.ModelField(ImageParams)

    def get_absolute_url(self):
        return ('products.versions', self.hostname, self.version,
            "containers", self.href)

class StageHref(Model):
    href = fields.AbsoluteUrlField(isAttribute = True)
    def get_absolute_url(self):
        return ('products.versions.stages', self.hostname, self.version,
            self.href)

class BuildDefinition(Model):
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
        name = "image-definitions"
    buildDefinitions = fields.ListField(BuildDefinition, displayName = 'image-definition')

class BuildTemplate(Model):
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
        name = 'image-type-definitions'
    buildTemplates = fields.ListField(BuildTemplate,
        displayName = 'image-type-definition')

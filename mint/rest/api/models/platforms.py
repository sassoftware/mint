#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

from mint.rest.api.models import builddefinitions
from mint.rest.modellib import Model
from mint.rest.modellib import fields


class _RepositoryUrlField(fields.AbstractUrlField):
    name = 'api'
    def _getUrl(self, parent, context):
        base = context.request.baseUrl
        if base.endswith('/api'):
            base = base[:-4]
        fqdn = parent.repositoryHostname
        if fqdn is None:
            return None
        # Must be able to distinguish a shortname from a single-label FQDN
        if '.' not in fqdn:
            fqdn += '.'
        return '%s/repos/%s/%s' % (base, fqdn, self.name)


class PlatformVersion(Model):
    class Meta(object):
        name = 'platformVersion'
    name = fields.CharField()
    version = fields.CharField()
    revision = fields.CharField()
    label = fields.CharField()
    ordering = fields.CharField()
    _platformId = fields.CharField()

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self._platformId,
                'platformVersions', '%s=%s' % (self.name, self.revision))

class EmptyPlatformVersion(Model):
    class Meta(object):
        name = 'platformVersion'

class PlatformVersions(Model):
    platformVersion = fields.ListField(PlatformVersion)

class Platform(Model):
    platformId = fields.CharField()
    platformTroveName = fields.CharField()
    repositoryHostname = fields.CharField()
    label = fields.CharField()
    platformVersion = fields.CharField()
    productVersion = fields.CharField()
    platformName = fields.CharField()
    platformUsageTerms = fields.CharField()
    mode = fields.CharField()
    enabled = fields.BooleanField()
    configurable = fields.BooleanField()
    abstract = fields.BooleanField()
    hidden = fields.BooleanField()
    mirrorPermission = fields.BooleanField()
    repositoryUrl = _RepositoryUrlField()
    upstream_url = fields.CharField()
    platformType = fields.CharField()
    imageTypeDefinitions = fields.UrlField('platforms.imageTypeDefinitions',
                                         ['platformId'])
    isPlatform = fields.BooleanField()
    platformVersions = fields.UrlField('platforms.platformVersions',
        ['platformId'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self.platformId)

class ProductPlatform(Platform):
    # This represents the platform object that is embedded inside a product.
    class Meta(object):
        name = 'platform'

    hostname = fields.CharField(display = False)
    def get_absolute_url(self):
        return ('products', self.hostname, 'versions', self.productVersion,
            'platform')

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')

class PlatformArchitecture(builddefinitions.Architecture):
    imageTypeDefinitions = fields.CharField(display=False)
    def get_absolute_url(self):
        return ('platforms', self.platform, 'imagesTypeDefinitions', 
            self.imageTypeDefinitions, 'architectures',
            self.id)

class PlatformFlavorSet(builddefinitions.FlavorSet):
    imageTypeDefinitions = fields.CharField(display=False)
    def get_absolute_url(self):
        return ('platforms', self.platform, 'imagesTypeDefinitions', 
            self.imageTypeDefinitions,'flavorsets',
            self.id)
    
class PlatformContainerFormat(builddefinitions.ContainerFormat):
    imageTypeDefinitions = fields.CharField(display=False)
    def get_absolute_url(self):
        return ('platforms', self.platform, 'imagesTypeDefinitions', 
            self.imageTypeDefinitions,'containers',
            self.id)

class PlatformBuildTemplate(builddefinitions.BuildTemplate):
    container = fields.ModelField(PlatformContainerFormat)
    architecture = fields.ModelField(PlatformArchitecture)
    flavorSet = fields.ModelField(PlatformFlavorSet)

    def get_absolute_url(self):
        return ('platforms.imageTypeDefinitions', self.platform, self.id)

class PlatformBuildTemplates(builddefinitions.BuildTemplates):
    buildTemplates = fields.ListField(PlatformBuildTemplate,
            displayName = 'imageTypeDefinition')

import products
from mint.rest.modellib import Model
from mint.rest.modellib import fields
from mint.rest.api.models import Descriptor

class PlatformSourceStatus(Model):
    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField()

class Source(Model):
    platformSourceId = fields.CharField()
    name = fields.CharField()
    platformId = fields.CharField()
    shortName = fields.CharField()
    sourceUrl = fields.CharField()
    username = fields.CharField()
    password = fields.CharField()
    defaultSource = fields.BooleanField()
    orderIndex = fields.IntegerField()
    platformSourceStatus = fields.UrlField(
                                'platforms.sources.status',
                                ['platformId', 'platformSourceId'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms.sources', self.platformId, self.platformSourceId)

class Sources(Model):
    source = fields.ListField(Source)

class Platform(Model):
    platformId = fields.CharField()
    hostname = fields.CharField()
    platformTroveName = fields.CharField()
    label = fields.CharField()
    platformVersion = fields.CharField()
    productVersion = fields.CharField()
    platformName = fields.CharField()
    enabled = fields.BooleanField()
    configurable = fields.BooleanField()
    repositoryUrl  = products.RepositoryRestUrlField()
    sources = fields.ModelField(Sources)
    platformMode = fields.CharField()
    sourceDescriptorConfig = fields.UrlField('platforms.sourceDescriptorConfig', ['platformId'])
    platformStatus = fields.UrlField('platforms.status', ['platformId'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self.platformId)

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')

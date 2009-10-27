import products
from mint.rest.modellib import Model
from mint.rest.modellib import fields

class PlatformSourceStatus(Model):
    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField()

class PlatformSource(Model):
    platformSourceId = fields.CharField()
    name = fields.CharField()
    shortName = fields.CharField(displayName='shortname')
    sourceUrl = fields.CharField()
    username = fields.CharField()
    password = fields.CharField()
    defaultSource = fields.BooleanField()
    orderIndex = fields.IntegerField()
    contentSourceType = fields.CharField()
    # platformSourceStatus = fields.UrlField(
                                # 'platforms.sources.status',
                                # ['platformId', 'shortName'])
    # configDescriptor = fields.UrlField(
                                # 'platforms.sources.descriptor', 
                                # ['platformId', 'shortName'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    # TODO: fix to new platformTypes structure
    def get_absolute_url(self):
        return ('sources.instances', self.contentSourceType, self.shortName)

class Sources(Model):
    platformSource = fields.ListField(PlatformSource)

class SourceTypes(Model):
    sourceType = fields.CharField()

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
    platformType = fields.CharField()
    platformStatus = fields.UrlField('platforms.status', ['platformId'])
    sourceTypes = fields.ListField(SourceTypes)

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self.platformId)

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')

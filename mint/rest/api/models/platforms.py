import products
from mint.rest.modellib import Model
from mint.rest.modellib import fields

class PlatformSourceStatus(Model):
    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField()

class PlatformSource(Model):
    class Meta(object):
        name = 'contentSource'

    contentSourceId = fields.CharField()
    name = fields.CharField()
    shortName = fields.CharField(displayName='shortname')
    sourceUrl = fields.CharField()
    username = fields.CharField()
    password = fields.CharField()
    defaultSource = fields.BooleanField()
    orderIndex = fields.IntegerField()
    contentSourceType = fields.CharField()
    contentSourceStatus = fields.UrlField(
                                'contentSources.instances.status',
                                ['contentSourceType', 'shortName'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('contentSources.instances', self.contentSourceType, self.shortName)

class SourceType(Model):
    class Meta(object):
        name = 'contentSourceType'
    contentSourceType = fields.CharField()
    instances = fields.UrlField('contentSources.instances', ['contentSourceType'])
    descriptor = fields.UrlField('contentSources.descriptor', ['contentSourceType'])
    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('contentSources', self.contentSourceType)

class ContentSources(Model):
    contentSourceType = fields.ListField(SourceType)

SourceInstance = PlatformSource

class SourceInstances(Model):
    class Meta(object):
        name = 'instances'
    instance = fields.ListField(SourceInstance, displayName='contentSource')

class SourceRef(Model):
    href = fields.AbsoluteUrlField(isAttribute=True)
    _contentSourceType = ''
    _shortName = ''
    def get_absolute_url(self):
        return ('contentSources.instances', self._contentSourceType, self._shortName) 

class SourceRefs(Model):
    sourceRef = fields.ListField(SourceRef, displayName='contentSource')

class SourceTypeRef(Model):
    href = fields.AbsoluteUrlField(isAttribute=True)
    contentSourceType = fields.CharField(display=False)
    def get_absolute_url(self):
        return ('contentSources', self.contentSourceType)

class SourceTypeRefs(Model):
    sourceTypeRef = fields.ListField(SourceTypeRef, displayName='contentSourceType')

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
    contentSources = fields.ModelField(SourceRefs)
    platformType = fields.CharField()
    platformStatus = fields.UrlField('platforms.status', ['platformId'])
    contentSourceTypes = fields.ModelField(SourceTypeRefs)

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self.platformId)

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')

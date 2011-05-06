#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

from mint import jobstatus
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


class Status(Model):
    connected = fields.BooleanField()
    valid = fields.BooleanField()
    message = fields.CharField()

class SourceStatus(Status):
    class Meta(object):
        name = 'contentSourceStatus'

class PlatformSourceStatus(Status):
    class Meta(object):
        name = 'platformSourceStatus'

class Source(Model):
    class Meta(object):
        name = 'contentSource'

    contentSourceId = fields.CharField()
    name = fields.CharField()
    shortName = fields.CharField(displayName='shortname')

    defaultSource = fields.BooleanField()
    orderIndex = fields.IntegerField()
    contentSourceType = fields.CharField()
    enabled = fields.BooleanField()
    contentSourceStatus = fields.UrlField(
                                'contentSources.instances.status',
                                ['contentSourceType', 'shortName'])
    resourceErrors = fields.UrlField(
                                'contentSources.instances.errors',
                                ['contentSourceType', 'shortName'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('contentSources.instances', self.contentSourceType, self.shortName)

class NuSource(Source):
    class Meta(object):
        name = 'contentSource'
    username = fields.CharField()
    password = fields.ProtectedField()

class SmtSource(Source):
    class Meta(object):
        name = 'contentSource'
    username = fields.CharField()
    password = fields.ProtectedField()
    sourceUrl = fields.CharField()

class RhnSource(Source):    
    class Meta(object):
        name = 'contentSource'
    username = fields.CharField()
    password = fields.ProtectedField()

class SatelliteSource(RhnSource):
    class Meta(object):
        name = 'contentSource'
    sourceUrl = fields.CharField()

class SourceType(Model):
    class Meta(object):
        name = 'contentSourceType'
    contentSourceType = fields.CharField()
    required = fields.BooleanField()
    singleton = fields.BooleanField()
    instances = fields.UrlField('contentSources.instances', ['contentSourceType'])
    configDescriptor = fields.UrlField('contentSources.descriptor', ['contentSourceType'])
    statusTest = fields.UrlField('contentSources.statusTest', ['contentSourceType'])
    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('contentSources', self.contentSourceType)

class SourceTypes(Model):
    class Meta(object):
        name = 'contentSourceTypes'
    contentSourceTypes = fields.ListField(SourceType, displayName='contentSourceType')

class ContentSourceInstances(Model):
    class Meta(object):
        name = 'contentSources'
    instance = fields.ListField(Source, displayName='contentSource')

class ContentSources(Model):
    contentSourceType = fields.ListField(SourceType)

class SourceInstances(Model):
    class Meta(object):
        name = 'instances'
    instance = fields.ListField(Source, displayName='contentSource')

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
    mirrorPermission = fields.BooleanField()
    repositoryUrl = _RepositoryUrlField()
    # contentSources = fields.ModelField(SourceRefs)
    contentSources = fields.UrlField('platforms.contentSources',
                                     ['platformId'])
    platformType = fields.CharField()
    platformStatus = fields.UrlField('platforms.status', ['platformId'])
    # contentSourceTypes = fields.ModelField(SourceTypeRefs)
    contentSourceTypes = fields.UrlField('platforms.contentSourceTypes',
                                         ['platformId'])
    load = fields.UrlField('platforms.load', ['platformId'])
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

class PlatformLoadStatusStub(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms.load', self.platformId, self.jobId)

class PlatformLoad(Model):
    loadUri = fields.CharField()
    jobId = fields.CharField()
    platformId = fields.IntegerField()
    job = fields.UrlField('platforms.load', ['platformId', 'jobId'])
    # platformLoadStatus = fields.ModelField(PlatformLoadStatusStub)

class PlatformLoadStatus(Model):
    code = fields.IntegerField()
    message = fields.CharField()
    isFinal = fields.BooleanField()


    def set_status(self, code=None, message=None):
        if code is not None:
            self.code = code
        if message is not None:
            self.message = message
        elif code is not None:
            # Use a default message if the code changed but no message was
            # provided.
            self.message = jobstatus.statusNames[self.code]
        self.isFinal = self.code in jobstatus.terminalStatuses

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

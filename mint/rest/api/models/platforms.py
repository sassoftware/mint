#
# Copyright (c) 2009 rPath, Inc.
#
# All rights reserved.
#

from mint import jobstatus
from mint.rest.modellib import Model
from mint.rest.modellib import fields


class _RepositoryUrlField(fields.AbstractUrlField):
    name = 'api'
    def _getUrl(self, parent, context):
        base = context.request.baseUrl
        if base.endswith('/api'):
            base = base[:-4]
        fqdn = parent.repositoryHostname
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
    contentSourceStatus = fields.UrlField(
                                'contentSources.instances.status',
                                ['contentSourceType', 'shortName'])
    resourceErrors = fields.UrlField(
                                'contentSources.instances.errors',
                                ['contentSourceType', 'shortName'])

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('contentSources.instances', self.contentSourceType, self.shortName)

class RhnSource(Source):    
    class Meta(object):
        name = 'contentSource'
    username = fields.CharField()
    password = fields.CharField()

class SatelliteSource(RhnSource):
    class Meta(object):
        name = 'contentSource'
    sourceUrl = fields.CharField()

class SourceType(Model):
    class Meta(object):
        name = 'contentSourceType'
    contentSourceType = fields.CharField()
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

class Platform(Model):
    platformId = fields.CharField()
    #hostname = fields.CharField()
    platformTroveName = fields.CharField()
    repositoryHostname = fields.CharField()
    label = fields.CharField()
    platformVersion = fields.CharField()
    productVersion = fields.CharField()
    platformName = fields.CharField()
    mode = fields.CharField()
    enabled = fields.BooleanField()
    configurable = fields.BooleanField()
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

    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms', self.platformId)

class Platforms(Model):
    platforms = fields.ListField(Platform, displayName='platform')

class PlatformLoadStatusStub(Model):
    id = fields.AbsoluteUrlField(isAttribute=True)

    def get_absolute_url(self):
        return ('platforms.load', self.platformId, self.jobId)

class PlatformLoad(Model):
    uri = fields.CharField()
    jobId = fields.IntegerField()
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


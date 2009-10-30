#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires
from mint.rest.db import contentsources
from mint.rest.middleware import auth
from mint.rest.modellib import converter

class SourceStatusController(base.BaseController):

    @auth.public
    def index(self, request, sourceType, shortName):
        return self.db.getSourceStatus(sourceType, shortName)

class SourceController(base.BaseController):
    modelName = 'shortName'

    urls = { 'status' : SourceStatusController }

    def _loadSourceModel(self, xml, sourceType):
        sourceModelClass = contentsources.contentSourceTypes[sourceType]
        source = converter.fromText('xml', xml,
                            sourceModelClass.model, None, None)
        return source                            

    @auth.public
    def index(self, request, sourceType):
        return self.db.getSources(sourceType, None)

    @auth.public
    def get(self, request, sourceType, shortName):
        return self.db.getSource(sourceType, shortName)

    @auth.public
    @requires('source', models.Source)
    def update(self, request, sourceType, shortName, source):
        source = self._loadSourceModel(request.body, sourceType)
        return self.db.updateSource(shortName, source)

    @auth.public
    @requires('source', models.Source)
    def create(self, request, sourceType, source):
        source = self._loadSourceModel(request.body, sourceType)
        return self.db.createSource(source)

    @auth.public
    def delete(self, request, sourceType, shortName):
        return self.db.deleteSource(shortName)

class SourceDescriptorController(base.BaseController):
    
    @auth.public
    def index(self, request, sourceType):
        return self.db.getSourceDescriptor(sourceType)

class SourceTypeController(base.BaseController):
    modelName = 'sourceType'

    urls = { 'instances' : SourceController,
             'descriptor' : SourceDescriptorController }

    @auth.public
    def index(self, request):
        return self.db.getSourceTypes()

    @auth.public
    def get(self, request, sourceType):
        return self.db.getSourceType(sourceType)

class PlatformStatusController(base.BaseController):

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformStatus(platformId)

class PlatformSourceController(base.BaseController):
    @auth.public
    def index(self, request, platformId):
        return self.db.getSources(None, platformId)

class PlatformSourceTypeController(base.BaseController):
    @auth.public
    def index(self, request, platformId):
        return self.db.getSourcesByPlatform(platformId)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'status' : PlatformStatusController,
             'contentSources' : PlatformSourceController,
             'contentSourceTypes' : PlatformSourceTypeController }

    @auth.public
    def index(self, request):
        return self.db.getPlatforms()

    @auth.public
    def get(self, request, platformId):        
        return self.db.getPlatform(platformId)

    @auth.public
    @requires('platform', models.Platform)
    def update(self, request, platformId, platform):
        return self.db.updatePlatform(platformId, platform)

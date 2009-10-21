#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

from mint.rest.middleware import auth

class PlatformSourceStatusController(base.BaseController):
    
    @auth.public
    def index(self, request, platformId, shortName):
        return self.db.getPlatformSourceStatus(shortName)

class PlatformSourceController(base.BaseController):
    modelName = 'shortName'

    urls = { 'status' : PlatformSourceStatusController }

    @auth.public
    def index(self, request, platformId):
        return self.db.listPlatformSources(platformId)

    @auth.public
    def get(self, request, platformId, shortName):
        return self.db.getPlatformSource(platformId, shortName)

    @auth.public
    @requires('source', models.PlatformSource)
    def create(self, request, platformId, source):
        return self.db.createPlatformSource(platformId, source)

    @auth.public
    @requires('source', models.PlatformSource)
    def update(self, request, platformId, shortName, source):
        return self.db.updatePlatformSource(platformId, 
                    shortName, source)

    @auth.public        
    def destroy(self, request, platformId, shortName):
        return self.db.deletePlatformSource(platformId, shortName)

class SourceDescriptorConfigController(base.BaseController):
    
    @auth.public
    def index(self, request, platformId):
        return self.db.getSourceDescriptorConfig(platformId)

class PlatformStatusController(base.BaseController):

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformStatus(platformId)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'sources' : PlatformSourceController,
             'sourceDescriptorConfig' : SourceDescriptorConfigController,
             'status' : PlatformStatusController }

    @auth.public
    def index(self, request):
        return self.db.listPlatforms()

    @auth.public
    def get(self, request, platformId):        
        return self.db.getPlatform(platformId)

    @auth.public
    @requires('platform', models.Platform)
    def update(self, request, platformId, platform):
        return self.db.updatePlatform(platformId, platform)

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models

from mint.rest.middleware import auth

class PlatformSourceController(base.BaseController):
    modelName = 'platformSourceId'

    @auth.public
    def index(self, request, platformId):
        return self.db.listPlatformSources(platformId)

    @auth.public
    def get(self, request, platformId, platformSourceId):
        return self.db.getPlatformSource(platformId, platformSourceId)

class SourceDescriptorConfigController(base.BaseController):
    
    @auth.public
    def index(self, request, platformId):
        return self.db.getSourceDescriptorConfig(platformId)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'sources' : PlatformSourceController,
             'sourceDescriptorConfig' : SourceDescriptorConfigController }

    @auth.public
    def index(self, request):
        return self.db.listPlatforms()

    @auth.public
    def get(self, request, platformId):        
        return self.db.getPlatform(platformId)



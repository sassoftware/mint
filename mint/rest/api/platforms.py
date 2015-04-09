#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires
from mint.rest.middleware import auth

class PlatformStatusController(base.BaseController):

    @auth.public
    @requires('platform', models.Platform)
    def process(self, request, platformId, platform):
        return self.db.getPlatformStatusTest(platform)

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformStatus(platformId)

class PlatformImageTypeController(base.BaseController):
    
    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformImageTypeDefs(request, platformId)

class PlatformVersionController(base.BaseController):
    modelName = 'platformVersionId'

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformVersions(platformId)

    @auth.public
    def get(self, request, platformId, platformVersionId):
        return self.db.getPlatformVersion(platformId, platformVersionId)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'status' : PlatformStatusController,
             'imageTypeDefinitions' : PlatformImageTypeController,
             'platformVersions' : PlatformVersionController,
           }

    @auth.public
    def index(self, request):
        return self.db.getPlatforms()

    @auth.public
    def get(self, request, platformId):        
        return self.db.getPlatform(platformId)

    @requires('platform', models.Platform)
    def create(self, request, platform):
        platformId =  self.db.createPlatform(platform)
        return self.db.getPlatform(platformId)

    @auth.admin
    @requires('platform', models.Platform)
    def update(self, request, platformId, platform):
        return self.db.updatePlatform(platformId, platform)

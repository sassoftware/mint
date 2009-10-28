#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

from mint.rest.middleware import auth

class SourceInstancesStatusController(base.BaseController):

    @auth.public
    def index(self, request, source, shortName):
        return self.db.getSourceInstanceStatus(source, shortName)

class SourceInstancesController(base.BaseController):
    modelName = 'shortName'

    urls = { 'status' : SourceInstancesStatusController }

    @auth.public
    def index(self, request, source):
        return self.db.getSourceInstances(source)

    @auth.public
    def get(self, request, source, shortName):
        return self.db.getSourceInstance(source, shortName)

    @auth.public
    @requires('sourceInstance', models.SourceInstance)
    def update(self, request, source, shortName, sourceInstance):
        return self.db.updateSourceInstance(shortName, sourceInstance)

class SourceDescriptorController(base.BaseController):
    
    @auth.public
    def index(self, request, source):
        return self.db.getSourceDescriptor(source)

class SourceController(base.BaseController):
    modelName = 'source'

    urls = { 'instances' : SourceInstancesController,
             'descriptor' : SourceDescriptorController }

    @auth.public
    def index(self, request):
        return self.db.getSources()

    @auth.public
    def get(self, request, source):
        return self.db.getSource(source)

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

class PlatformStatusController(base.BaseController):

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformStatus(platformId)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'status' : PlatformStatusController }

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

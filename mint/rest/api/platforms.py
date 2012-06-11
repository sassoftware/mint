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

def _loadSourceModel(xml, sourceType):
    sourceModelClass = contentsources.contentSourceTypes[sourceType]
    source = converter.fromText('xml', xml,
                        sourceModelClass.model, None, None)
    return source                            

class SourceStatusController(base.BaseController):

    @auth.admin
    def index(self, request, sourceType, shortName):
        return self.db.getSourceStatusByName(sourceType, shortName)

class SourceErrorsController(base.BaseController):
    modelName = 'errorId'

    @auth.admin
    def index(self, request, sourceType, shortName):
        return self.db.getPlatformContentErrors(sourceType, shortName)

    @auth.admin
    def get(self, request, sourceType, shortName, errorId):
        return self.db.getPlatformContentError(sourceType, shortName, errorId)

    @auth.admin
    @requires('resourceError', models.ResourceError)
    def update(self, request, sourceType, shortName, errorId, resourceError):
        return self.db.updatePlatformContentError(sourceType, shortName,
            errorId, resourceError)

class SourceController(base.BaseController):
    modelName = 'shortName'

    urls = { 'status' : SourceStatusController,
             'errors' : SourceErrorsController, }

    @auth.admin
    def index(self, request, sourceType):
        return self.db.getSources(sourceType)

    @auth.admin
    def get(self, request, sourceType, shortName):
        return self.db.getSource(shortName)

    @auth.admin
    @requires('source', models.Source)
    def update(self, request, sourceType, shortName, source):
        source = _loadSourceModel(request.body, sourceType)
        return self.db.updateSource(shortName, source)

    @auth.admin
    @requires('source', models.Source)
    def create(self, request, sourceType, source):
        source = _loadSourceModel(request.body, sourceType)
        return self.db.createSource(source)

    @auth.admin
    def destroy(self, request, sourceType, shortName):
        return self.db.deleteSource(shortName)

class SourceTypeDescriptorController(base.BaseController):
    
    @auth.admin
    def index(self, request, sourceType):
        return self.db.getSourceTypeDescriptor(sourceType)

class SourceTypeStatusTest(base.BaseController):
    @auth.admin
    @requires('source', models.Source)
    def process(self, request, sourceType, source):
        source = _loadSourceModel(request.body, sourceType)
        return self.db.getSourceStatus(source)

class SourceTypeController(base.BaseController):
    modelName = 'sourceType'

    urls = { 'instances' : SourceController,
             'descriptor' : SourceTypeDescriptorController,
             'statusTest' : SourceTypeStatusTest }

    def index(self, request):
        return self.db.getSourceTypes()

    def get(self, request, sourceType):
        return self.db.getSourceType(sourceType)

class PlatformStatusController(base.BaseController):

    @auth.public
    @requires('platform', models.Platform)
    def process(self, request, platformId, platform):
        return self.db.getPlatformStatusTest(platform)

    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformStatus(platformId)

class PlatformSourceController(base.BaseController):

    @auth.admin
    def index(self, request, platformId):
        return self.db.getSourcesByPlatform(platformId)

class PlatformSourceTypeController(base.BaseController):

    def index(self, request, platformId):
        return self.db.getSourceTypesByPlatform(platformId)

class PlatformImageTypeController(base.BaseController):
    
    @auth.public
    def index(self, request, platformId):
        return self.db.getPlatformImageTypeDefs(request, platformId)

class PlatformLoadController(base.BaseController):
    modelName = 'jobId'
    
    @auth.admin
    def get(self, request, platformId, jobId):
        return self.db.getPlatformLoadStatus(platformId, jobId)

    @auth.admin
    @requires('platformLoad', models.PlatformLoad)
    def create(self, request, platformId, platformLoad):
        return self.db.loadPlatform(platformId, platformLoad)

class PlatformController(base.BaseController):
    modelName = "platformId"

    urls = { 'status' : PlatformStatusController,
             'contentSources' : PlatformSourceController,
             'contentSourceTypes' : PlatformSourceTypeController,
             'imageTypeDefinitions' : PlatformImageTypeController,
             'load' : PlatformLoadController,
           }

    @auth.public
    def index(self, request):
        return self.db.getPlatforms()

    @auth.public
    def get(self, request, platformId):        
        return self.db.getPlatform(platformId)

    @auth.admin
    @requires('platform', models.Platform)
    def update(self, request, platformId, platform):
        return self.db.updatePlatform(platformId, platform)

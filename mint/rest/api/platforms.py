#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
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

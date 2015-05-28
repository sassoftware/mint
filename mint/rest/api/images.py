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
from mint.rest.middleware import auth


class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {
            'files' : {'GET': 'getFiles'},
            'stop'  : {'POST' : 'stop'},
            'status': {'GET': 'getStatus'},
            'buildLog': {'GET': 'getBuildLog'},
            }

    @auth.public
    def index(self, request, hostname):
        return self.db.listImagesForProduct(hostname)

    @auth.public
    def get(self, request, hostname, imageId):
        return self.db.getImageForProduct(hostname, imageId)

    def stop(self, request, hostname, imageId):
        return self.db.stopImageJob(hostname, imageId)

    @auth.public
    def getBuildLog(self, request, hostname, imageId):
        return self.db.getImageFile(hostname, imageId, 'build.log',
                asResponse=True)

    @auth.public
    def getFiles(self, request, hostname, imageId):
        return self.db.listFilesForImage(hostname, imageId)

    @auth.public
    def getStatus(self, request, hostname, imageId):
        return self.db.getImageStatus(hostname, imageId)

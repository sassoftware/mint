#
# Copyright (c) SAS Institute Inc.
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

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from mint.rest.api import requires
from mint.rest.api import base
from mint.rest.api import models
from mint.rest.errors import PermissionDeniedError
from mint.rest.middleware import auth
from restlib.response import Response


class ProductImageFilesController(base.BaseController):
    modelName = 'fileName'

    def index(self, hostname, imageId):
        return self.db.listFilesForImage(hostname, imageId)

    def destroy_all(self, request, hostname, imageId):
        return self.db.deleteImageFilesForProduct(hostname, imageId)

class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {'files' : ProductImageFilesController,
            'stop'  : {'POST' : 'stop'},
            'status': {'GET': 'getStatus'},
            'buildLog': {'GET': 'getBuildLog', 'POST': 'postBuildLog'},
            }

    @auth.public
    def index(self, request, hostname):
        return self.db.listImagesForProduct(hostname)

    @auth.public
    def get(self, request, hostname, imageId):
        return self.db.getImageForProduct(hostname, imageId)

    def destroy(self, request, hostname, imageId):
        self.db.deleteImageForProduct(hostname, imageId)

    def stop(self, request, hostname, imageId):
        return self.db.stopImageJob(hostname, imageId)

    # job API
    @staticmethod
    def _getImageToken(request):
        imageToken = request.headers.get('X-rBuilder-OutputToken')
        if not imageToken:
            raise PermissionDeniedError()
        return imageToken

    @auth.public
    def getStatus(self, request, hostname, imageId):
        return self.db.getImageStatus(hostname, imageId)

    @auth.public
    def getBuildLog(self, request, hostname, imageId):
        return self.db.getImageFile(hostname, imageId, 'build.log',
                asResponse=True)

    @auth.public
    def postBuildLog(self, request, hostname, imageId):
        imageToken = self._getImageToken(request)
        data = request.read()
        self.db.appendImageFile(hostname, imageId, 'build.log', imageToken,
                data)

        # 204 No Content
        return Response(status=204)

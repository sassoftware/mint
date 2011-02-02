#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from conary.lib import sha1helper

from mint.lib import data as datatypes
from mint.rest.api import requires
from mint.rest.api import base
from mint.rest.api import models
from mint.rest.errors import PermissionDeniedError
from mint.rest.middleware import auth
from restlib.response import Response


class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {
            'files' : {
                'GET': 'getFiles',
                'PUT': 'setFiles',
                'DELETE': 'deleteFiles',
                },
            'stop'  : {'POST' : 'stop'},
            'status': {'GET': 'getStatus', 'PUT': 'setStatus'},
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

    @requires('image', models.Image)
    def create(self, request, hostname, image):
        outputToken = sha1helper.sha1ToString(file('/dev/urandom').read(20))
        buildData = [('outputToken', outputToken, datatypes.RDT_STRING)]
        imageId = self.db.createImage(hostname, image, buildData=buildData)
        self.db.uploadImageFiles(hostname, image, outputToken=outputToken)
        return self.get(request, hostname, imageId)

    def stop(self, request, hostname, imageId):
        return self.db.stopImageJob(hostname, imageId)

    @auth.public
    def getBuildLog(self, request, hostname, imageId):
        return self.db.getImageFile(hostname, imageId, 'build.log',
                asResponse=True)

    @auth.public
    def getFiles(self, request, hostname, imageId):
        return self.db.listFilesForImage(hostname, imageId)

    def deleteFiles(self, request, hostname, imageId):
        return self.db.deleteImageFilesForProduct(hostname, imageId)

    @auth.public
    def getStatus(self, request, hostname, imageId):
        return self.db.getImageStatus(hostname, imageId)

    # job API
    @auth.tokenRequired
    @requires('status', models.ImageStatus)
    def setStatus(self, request, hostname, imageId, status):
        return self.db.setImageStatus(hostname, imageId, request.imageToken,
                status)

    @auth.tokenRequired
    @requires('files', models.ImageFileList)
    def setFiles(self, request, hostname, imageId, files):
        return self.db.setFilesForImage(hostname, imageId, request.imageToken,
                files)

    @auth.tokenRequired
    def postBuildLog(self, request, hostname, imageId):
        data = request.read()
        self.db.appendImageFile(hostname, imageId, 'build.log',
                request.imageToken, data)

        # 204 No Content
        return Response(status=204)

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#
from mint.rest.api import requires
from mint.rest.api import base
from mint.rest.api import models
from mint.rest.middleware import auth

class ProductImageFilesController(base.BaseController):
    modelName = 'fileName'

    def index(self, hostname, imageId):
        return self.db.listFilesForImage(hostname, imageId)

    def destroy_all(self, request, hostname, imageId):
        return self.db.deleteImageFilesForProduct(hostname, imageId)

class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {'files' : ProductImageFilesController,
            'stop'  : {'POST' : 'stop'}}

    def index(self, request, hostname):
        return self.db.listImagesForProduct(hostname)

    def get(self, request, hostname, imageId):
        return self.db.getImageForProduct(hostname, imageId)

    def destroy(self, request, hostname, imageId):
        self.db.deleteImageForProduct(hostname, imageId)

    def stop(self, request, hostname, imageId):
        return self.db.stopImageJob(hostname, imageId)

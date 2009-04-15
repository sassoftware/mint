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


class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {'files' : ProductImageFilesController,
            'stop'  : {'POST' : 'stop'}}

    def index(self, request, hostname):
        return self.db.listImagesForProduct(hostname)

    def get(self, request, hostname, imageId):
        update = int(request.GET.get('update', 0))
        return self.db.getImageForProduct(hostname, imageId, update=update)

    def stop(self, request, hostname, imageId):
        return self.db.stopImageJob(hostname, imageId)

class ProductReleasesController(base.BaseController):
    modelName = 'releaseId'

    urls = {'images' : {'GET' : 'images',
                        'POST' : 'addImage',
                        'PUT'  : 'setImages'},
            'publish' : {'POST' : 'publish'},
            'unpublish' : {'POST' : 'unpublish'}}

    @auth.public
    def index(self, request, hostname):
        return self.db.listReleasesForProduct(hostname)

    @auth.public
    def get(self, request, hostname, releaseId):
        return self.db.getReleaseForProduct(hostname, releaseId)

    def destroy(self, request, hostname, releaseId):
        return self.db.deleteRelease(hostname, releaseId)

    @requires('release', models.UpdateRelease)
    def create(self, request, hostname, release):
        releaseId = self.db.createRelease(hostname, release.name,
                                          release.description,
                                          release.version,
                                          [ x.imageId for x in release.imageIds])
        return self.get(request, hostname, releaseId)

    @requires('release', models.UpdateRelease)
    def update(self, request, hostname, releaseId, release):
        self.db.updateRelease(hostname, releaseId, release.name,
                              release.description,
                              release.version,
                              release.published,
                              release.shouldMirror,
                              [x.imageId for x in release.imageIds])
        return self.get(request, hostname, releaseId)

    @requires('publishOptions', models.PublishOptions)
    def publish(self, request, hostname, releaseId):
        self.db.publishRelease(hostname, releaseId, publishOptions.shouldMirror)
        return self.get(request, hostname, releaseId)

    def unpublish(self, request, hostname, releaseId):
        self.db.unpublishRelease(hostname, releaseId)
        return self.get(request, hostname, releaseId)

    @auth.public
    def images(self, request, hostname, releaseId):
        update = int(request.GET.get('update', 0))
        return self.db.listImagesForRelease(hostname, releaseId, update=update)

    @requires('image', models.ImageId)
    def addImage(self, request, hostname, releaseId, image):
        self.db.addImageToRelease(hostname, releaseId, image.imageId)
        return self.get(request, hostname, releaseId)

    @requires('images', models.ImageList)
    def setImages(self, request, hostname, releaseId, images):
        self.db.updateImagesForRelease(hostname, releaseId,
			       [x.imageId for x in images.images])
        return self.get(request, hostname, releaseId)

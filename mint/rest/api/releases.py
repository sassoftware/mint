#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import os

from mint.rest.api import requires
from mint.rest.api import base
from mint.rest.api import models
from mint.rest.middleware import auth

class ProductReleasesController(base.BaseController):
    modelName = 'releaseId'

    urls = {'images' : {'GET' : 'images',
                        'POST' : 'addImage',
                        'PUT'  : 'setImages'},
            'publish' : {'POST' : 'publish'},
            'unpublish' : {'POST' : 'unpublish'}}

    @auth.public
    def index(self, request, hostname):
        limit = request.GET.get('limit', None)
        if limit:
            limit = int(limit)
        return self.db.listReleasesForProduct(hostname, limit=limit)

    @auth.public
    def get(self, request, hostname, releaseId):
        return self.db.getReleaseForProduct(hostname, releaseId)

    def destroy(self, request, hostname, releaseId):
        self.db.deleteRelease(hostname, releaseId)
        return self.index(request, hostname)

    @requires('release', models.UpdateRelease)
    def create(self, request, hostname, release):
        if release.imageIds is not None:
            imageIds = [ x.imageId for x in release.imageIds]
        else:
            imageIds = []

        releaseId = self.db.createRelease(hostname, release.name,
                                          release.description,
                                          release.version, imageIds)
        return self.get(request, hostname, releaseId)

    @requires('release', models.UpdateRelease)
    def update(self, request, hostname, releaseId, release):
        if release.imageIds is not None:
            imageIds = [ x.imageId for x in release.imageIds]
        else:
            imageIds = None
        self.db.updateRelease(hostname, releaseId, release.name,
                              release.description,
                              release.version,
                              release.published,
                              release.shouldMirror, imageIds=None)
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
        return self.db.listImagesForRelease(hostname, releaseId)

    @requires('image', models.ImageId)
    def addImage(self, request, hostname, releaseId, image):
        if image.id:
            imageId = os.path.basename(image.id)
        else:
            imageId = image.imageId
        self.db.addImageToRelease(hostname, releaseId, imageId)
        return self.db.getImageForProduct(hostname, imageId)

    @requires('images', models.ImageList)
    def setImages(self, request, hostname, releaseId, images):
        # note - this should not be necessary but is due to some
        # behavior in xobj when the top-level element is an empty list.
        if images.images is None:
            images.images = []
        self.db.updateImagesForRelease(hostname, releaseId,
			       [x.imageId for x in images.images])
        return self.images(request, hostname, releaseId)

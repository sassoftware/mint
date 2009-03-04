
from mint.rest.api import base

class ProductImageFilesController(base.BaseController):
    modelName = 'fileName'

    def index(self, hostname, imageId):
        return self.db.listFilesForImage(hostname, imageId)


class ProductImagesController(base.BaseController):

    modelName = 'imageId'

    urls = {'files' : ProductImageFilesController}

    def index(self, request, hostname):
        return self.db.listImagesForProduct(hostname)

    def get(self, request, hostname, imageId):
        return self.db.getImageForProduct(hostname, imageId)

class ProductReleasesController(base.BaseController):
    modelName = 'releaseId'

    urls = {'images' : {'GET' : 'images'}}

    def index(self, request, hostname):
        return self.db.listReleasesForProduct(hostname)

    def get(self, request, hostname, releaseId):
        return self.db.getReleaseForProduct(hostname, releaseId)

    def images(self, request, hostname, releaseId):
        return self.db.listImagesForRelease(hostname, releaseId)


from mint.rest.api import base

class ProductBuildFilesController(base.BaseController):
    modelName = 'fileName'

    def index(self, hostname, buildId):
        return self.db.listFilesForBuild(hostname, buildId)


class ProductBuildsController(base.BaseController):

    modelName = 'buildId'

    urls = {'files' : ProductBuildFilesController}

    def index(self, request, hostname):
        return self.db.listBuildsForProduct(hostname)

    def get(self, request, hostname, buildId):
        return self.db.getBuildForProduct(hostname, buildId)

class ProductReleasesController(base.BaseController):
    modelName = 'releaseId'

    urls = {'builds' : {'GET' : 'builds'}}

    def index(self, request, hostname):
        return self.db.listReleasesForProduct(hostname)

    def get(self, request, hostname, releaseId):
        return self.db.getReleaseForProduct(hostname, releaseId)

    def builds(self, request, hostname, releaseId):
        return self.db.listBuildsForRelease(hostname, releaseId)

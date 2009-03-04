from restlib import response

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

class ProductVersionStages(base.BaseController):
    modelName = 'stageName'

    urls = {'images' : dict(GET='getImages')}
    
    def index(self, request, hostname, version):
        return self.db.getProductVersionStages(hostname, version)

    def get(self, request, hostname, version, stageName):
        return self.db.getProductVersionStage(hostname, version, stageName)

    def getImages(self, request, hostname, version, stageName):
        return self.db.getProductVersionStageImages(hostname, version, stageName)

class ProductVersionController(base.BaseController):

    modelName = 'version'
    urls = {'platform'   : dict(GET='getPlatform',
                                PUT='setPlatform',
                                POST='updatePlatform'),
            'stages'     : ProductVersionStages,
            'definition' : dict(GET='getDefinition', 
                                PUT='setDefinition'),
            'images'     : dict(GET='getImages')}

    def index(self, request, hostname):
        return self.db.listProductVersions(hostname)

    def get(self, request, hostname, version):
        return self.db.getProductVersion(hostname, version)

    @requires('productVersion', models.ProductVersion)
    def update(self, request, hostname, version, productVersion):
        return self.db.updateProductVersion(hostname, version, productVersion)
        
    @requires('productVersion', models.ProductVersion)
    def create(self, request, hostname, productVersion):
        self.db.createProductVersion(hostname, productVersion)
        return response.RedirectResponse(
                           self.url(request, 'products.versions', 
                                    hostname, productVersion.name))

    def getImages(self, request, hostname, version):
        return self.db.getProductVersionImages(hostname, version)

    def getPlatform(self, request, hostname, version):
        return self.db.getProductVersionPlatform(hostname, version)

    @requires('platform', models.Platform)
    def setPlatform(self, request, hostname, version, platform):
        self.db.rebaseProductVersionPlatform(hostname, version, platform.label)
        return response.RedirectResponse(
                        self.url(request, 'products.versions.platform', 
                                 hostname, version))

    def updatePlatform(self, request, hostname, version):
        self.db.rebaseProductVersionPlatform(hostname, version)
        return response.RedirectResponse(
                        self.url(request, 'products.versions.platform', 
                                 hostname, version))

    def getDefinition(self, request, hostname, version):
        pd = self.db.getProductVersionDefinition(hostname, version)
        return response.Response(self._fromProddef(pd))

    def setDefinition(self, request, hostname, version):
        pd = self._toProddef(request)
        self.db.setProductVersionDefinition(hostname, version, pd)
        return response.RedirectResponse(
                    self.url(request, 'products.versions.definition', 
                             hostname, version))

    def _toProddef(self, request):
        from rpath_common.proddef import api1 as proddef
        return proddef.ProductDefinition(fromStream=request.read())

    def _fromProddef(self, pd):
        import cStringIO as StringIO
        sio = StringIO.StringIO()
        pd.serialize(sio)
        return sio.getvalue()

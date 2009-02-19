
from restlib import response

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

class ProductVersionController(base.BaseController):

    modelName = 'version'
    urls = {'platform'   : dict(GET='getPlatform',
                                PUT='setPlatform',
                                POST='updatePlatform'),
            'stages'     : dict(GET='getStages'),
            'definition' : dict(GET='getDefinition', 
                                PUT='setDefinition')}

    def index(self, request, hostname):
        return self.db.listProductVersions(hostname)

    def get(self, request, hostname, version):
        return self.db.getProductVersion(hostname, version)

    @requires('productVersion', models.ProductVersion)
    def update(self, request, hostname, version, productVersion):
        return self.db.updateProductVersion(hostname, version, productVersion)

    def getStages(self, request, hostname, version):
        return self.db.getProductVersionStages(hostname, version)

    def getPlatform(self, request, hostname, version):
        return self.db.getProductVersionPlatform(hostname, version)

    @requires('platform', models.Platform)
    def setPlatform(self, request, hostname, version, platform):
        self.db.rebaseProductVersionPlatform(hostname, version, platform.label)
        return response.RedirectResponse(self.url(request, 'products.versions.platform', 
                                                  hostname, version))

    def updatePlatform(self, request, hostname, version):
        self.db.rebaseProductVersionPlatform(hostname, version)
        return response.RedirectResponse(self.url(request, 'products.versions.platform', 
                                                  hostname, version))

    def getDefinition(self, request, hostname, version):
        pd = self.db.getProductVersionDefinition(hostname, version)
        return response.Response(self._fromProddef(pd))

    def setDefinition(self, request, hostname, version):
        pd = self._toProddef(request)
        self.db.setProductVersionDefinition(hostname, version, pd)
        return response.RedirectResponse(self.url(request, 'products.versions.definition', 
                                                  hostname, version))

    def _toProddef(self, request):
        from rpath_common.proddef import api1 as proddef
        return proddef.ProductDefinition(fromStream=request.read())

    def _fromProddef(self, pd):
        import cStringIO as StringIO
        sio = StringIO.StringIO()
        pd.serialize(sio)
        return sio.getvalue()
       

class ProductMemberController(base.BaseController):

    modelName = 'username'

    def index(self, request, hostname):
        return self.db.listProductMembers(hostname)

    def get(self, request, hostname, username):
        return self.db.getProductMembership(hostname, username)

    @requires('membership', models.UpdateMembership)
    def update(self, request, hostname, username, membership):
        self.db.setMemberLevel(hostname, username, membership.level)
        return response.RedirectResponse(self.url(request, 'products.members', 
                                                  hostname, username))

    def destroy(self, request, hostname, username):
        self.db.deleteMember(hostname, username)
        return response.RedirectResponse(self.url(request, 'products.members', 
                                                  hostname))

class ProductController(base.BaseController):
    modelName = 'hostname'

    urls = {'versions' : ProductVersionController,
            'members'  : ProductMemberController }

    def index(self, request):
        return self.db.listProducts()

    def get(self, request, hostname):
        return self.db.getProduct(hostname)

    @requires('product', models.Product)
    def create(self, request, product):
        self.db.createProduct(product)
        return response.RedirectResponse(self.url(request, 'products', 
                                                  product.hostname))

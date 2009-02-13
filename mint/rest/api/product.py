from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import requires

class ProductVersionController(base.BaseController):

    modelName = 'version'

    def index(self, request, hostname):
        return self.db.listProductVersions(hostname)

    def get(self, request, hostname, version):
        return self.db.getProductVersions(hostname)


class ProductMemberController(base.BaseController):

    modelName = 'username'

    def index(self, request, hostname):
        return self.db.listProductMembers(hostname)

    def get(self, request, hostname, username):
        return self.db.getProductMembership(hostname, username)


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
        return product

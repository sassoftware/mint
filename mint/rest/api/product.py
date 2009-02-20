
from restlib import response

from mint.rest.api import base
from mint.rest.api import models
from mint.rest.api import productversion
from mint.rest.api import requires


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

    urls = {'versions' : productversion.ProductVersionController,
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

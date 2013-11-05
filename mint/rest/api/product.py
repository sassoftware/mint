#
# Copyright (c) SAS Institute Inc.
#

from mint import mint_error
from mint.rest import errors
from mint.rest.api import base
from mint.rest.api import images
from mint.rest.api import models
from mint.rest.api import productversion
from mint.rest.api import repos
from mint.rest.api import requires

from mint.rest.middleware import auth

class ProductMemberController(base.BaseController):

    modelName = 'username'

    def index(self, request, hostname):
        return self.db.listProductMembers(hostname)

    def get(self, request, hostname, username):
        return self.db.getProductMembership(hostname, username)

    @requires('membership', models.UpdateMembership)
    def update(self, request, hostname, username, membership):
        self.db.setMemberLevel(hostname, username, membership.level)
        return self.get(request, hostname, username)

    def destroy(self, request, hostname, username):
        self.db.deleteMember(hostname, username)
        return self.index(request, hostname)


class ProductController(base.BaseController):
    modelName = 'hostname'

    urls = {'versions'   : productversion.ProductVersionController,
            'members'    : ProductMemberController,
            'repos'      : repos.RepositoryController,
            'images'     : images.ProductImagesController,
            }

    @auth.public
    def index(self, request):
        limit = request.GET.get('limit', None)
        start = request.GET.get('start', None)
        search = request.GET.get('search', None)
        role = request.GET.get('role', None)
        prodtype = request.GET.get('prodtype', None)
        if limit:
            limit = int(limit)
        if start:
            start = int(start)
        if isinstance(role, basestring):
            role = [role]
        return self.db.listProducts(limit=limit, start=start, search=search,
                roles=role, prodtype=prodtype)

    @auth.public
    def get(self, request, hostname):
        return self.db.getProduct(hostname)

    @requires('product', models.Product)
    def update(self, request, hostname, product):
        self.db.updateProduct(hostname, product)
        return self.get(request, hostname)

    @requires('product', models.Product)
    def create(self, request, product):
        try:
            self.db.createProduct(product)
        except (mint_error.InvalidShortname, mint_error.InvalidHostname), e:
            raise errors.InvalidItem(str(e))

        return self.get(request, product.hostname)

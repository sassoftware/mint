#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from restlib import response

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
        return response.SeeOtherResponse(self.url(request, 'products.members', 
                                                  hostname, username))

    def destroy(self, request, hostname, username):
        self.db.deleteMember(hostname, username)
        return response.SeeOtherResponse(self.url(request, 'products.members', 
                                                  hostname))

class ProductController(base.BaseController):
    modelName = 'hostname'

    urls = {'versions'   : productversion.ProductVersionController,
            'members'    : ProductMemberController,
            'repos'      : repos.RepositoryController,
            'images'     : images.ProductImagesController,
            'releases'   : images.ProductReleasesController  }

    @auth.public
    def index(self, request):
        limit = request.GET.get('limit', None)
        start = request.GET.get('start', None)
        search = request.GET.get('search', None)
        if limit:
            limit = int(limit)
        if start:
            start = int(start)
        return self.db.listProducts(limit=limit, start=start, search=search)

    @auth.public
    def get(self, request, hostname):
        return self.db.getProduct(hostname)

    @requires('product', models.Product)
    def create(self, request, product):
        self.db.createProduct(product)
        return response.SeeOtherResponse(self.url(request, 'products', 
                                                  product.hostname))

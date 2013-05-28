#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base

class UserController(base.BaseController):
    modelName = 'username'

    urls = {'products' : 'listProducts',
            }

    def index(self, request):
        return self.db.listUsers()

    def get(self, request, username):
        return self.db.getUser(username)
    
    #actual controllers need to be added to handle the product membership 
    #and groups that a user belongs.  This will likely intersect with RBAC.
    def listProducts(self, request, username):
        return self.db.listMembershipsForUser(username)

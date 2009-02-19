from mint.rest.api import base

class UserController(base.BaseController):
    modelName = 'username'

    urls = {'products' : 'listProducts',
            'groups'   : 'listGroups'}

    def index(self, request):
        return self.db.listUsers()

    def get(self, request, username):
        return self.db.getUser(username)
    
    def listProducts(self, request, username):
        return self.db.listMembershipsForUser(username)

    def listGroups(self, request, username):
        return self.db.listUserGroupsForUser(username)

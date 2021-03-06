#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


from django.http import HttpResponse, HttpResponseRedirect
from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml, access
from mint.django_rest.rbuilder.rbac.rbacauth import rbac, manual_rbac
from mint.django_rest.rbuilder.errors import PermissionDenied
from mint.django_rest.rbuilder.querysets import models as querymodels
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import \
   READMEMBERS, MODMEMBERS

def rbac_can_read_user(view, request, user_id, *args, **kwargs):
    obj = view.mgr.getUser(user_id)
    user = request._authUser
    if obj.pk == user.pk:
        # you can always read yourself
        return True 
    return view.mgr.userHasRbacPermission(user, obj, READMEMBERS)

def rbac_can_write_user(view, request, user_id, *args, **kwargs):
    obj = view.mgr.getUser(user_id)
    user = request._authUser
    if obj.pk == user.pk:
        # you can always update yourself
        # TODO: but you can't delete yourself unless admin
        return True
    return view.mgr.userHasRbacPermission(user, obj, MODMEMBERS)

class UsersService(service.BaseService):
    
    # manual rbac
    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request, user_id=None):
        qs = querymodels.QuerySet.objects.get(name='All Users')
        url = '/api/v1/query_sets/%s/all%s' % (qs.pk, request.params)
        return HttpResponseRedirect(url)

    @access.admin
    @requires('user', save=False)
    @return_xml
    def rest_POST(self, request, user):
        # TODO: verify we have a user
        if not user.user_name:
            return HttpResponse(status=400)
        return self.mgr.addUser(user, request._authUser)

class UserService(service.BaseService):

    # manual rbac
    @rbac(manual_rbac)
    @return_xml
    def rest_GET(self, request, user_id):
         if rbac_can_read_user(self, request, user_id):
             return self.get(user_id)
         raise PermissionDenied()

    def get(self, user_id):
        # if user_id is None then we have bypassed rbac
        # (which is manually run inside rest_GET)
        return self.mgr.getUser(user_id)

    @rbac(rbac_can_write_user)
    @requires('user', save=False)
    @return_xml
    def rest_PUT(self, request, user_id, user):
        oldUser = self.mgr.getUser(user_id)
        if oldUser.pk != user.pk:
            raise PermissionDenied()
        return self.mgr.updateUser(user_id, user, request._authUser)

    @access.admin
    def rest_DELETE(self, request, user_id):
        self.mgr.deleteUser(user_id, request._authUser)
        return HttpResponse(status=204)

class SessionService(service.BaseService):

    @access.anonymous
    @return_xml
    def rest_GET(self, request):
        return self.mgr.getSessionInfo()

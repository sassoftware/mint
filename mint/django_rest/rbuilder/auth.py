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


from conary.repository.netrepos.auth_tokens import ValidPasswordToken
from mint.django_rest.rbuilder.users.models import User
from mint.django_rest.rbuilder.manager import rbuildermanager
from django.db import transaction
from django.db.utils import IntegrityError
from mint.lib import auth_client
from hashlib import md5
import time


def getAuth(request):
    token = request.META['mint.authToken'][:2]
    if token[0] == 'anonymous':
        token = (None, None)
    return token


def isAdmin(user):
    if not isinstance(user, User):
        return False
    return user.is_admin

def isAuthenticated(user):
     if user is not None and isinstance(user, User):
         return True
     return False

class rBuilderBackend(object):
    supports_anonymous_user = False
    supports_inactive_user = False
    supports_object_permissions = False

    def authenticate(self, username=None, password=None, mintConfig=None):
        try:
            user = User.objects.get(user_name=username, deleted=False)
        except User.DoesNotExist:
            return None
        if password is ValidPasswordToken:
            self.update_login_time(user)
            return user
        if user.passwd and user.salt:
            salt = user.salt.decode('hex')
            m = md5(salt + password)
            if (m.hexdigest() == user.passwd):
                self.update_login_time(user)
                return self.updateUserOnLogin(user)
        elif mintConfig:
            client = auth_client.getClient(mintConfig.authSocket)
            if client.checkPassword(username, password):
                self.update_login_time(user)
                return self.updateUserOnLogin(user)
        return None

    def updateUserOnLogin(self, user):
        # ensure old users and RAPA new users always have MyQuerysets
        # so the resources they create are not unhomed
        mgr = rbuildermanager.RbuilderManager()
        if user.is_admin and not user.can_create: 
            user.can_create = True
            user.save()
            tsid = transaction.savepoint()
            try:
                mgr.getOrCreateIdentityRole(user, user)
            except IntegrityError:
                # in event of two API parallel requests 
                # it's ok if this doesn't succeed
                transaction.savepoint_rollback(tsid)
                
        mgr.configureMyQuerysets(user, user)
        return user


    def update_login_time(self, user):
        '''
        user logins already keep this updated (elsewhere), 
        direct API hits also need it updated
        '''
        user.last_login_date = time.time()
        user.save()

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id, deleted=False)
        except User.DoesNotExist:
            return None


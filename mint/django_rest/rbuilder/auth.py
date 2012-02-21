#
# Copyright (c) 2011 rPath, Inc.
#
from conary.repository.netrepos.netauth import ValidPasswordToken
from mint.django_rest.rbuilder.models import Sessions
from mint.django_rest.rbuilder.users.models import User
from mint.django_rest.rbuilder.manager import rbuildermanager
from django.db import transaction
from django.db.utils import IntegrityError
from mint.lib import auth_client
from hashlib import md5
import base64
import cPickle
import time

def getCookieAuth(request):
    # the pysid cookie contains the session reference that we can use to
    # look up the proper credentials
    # we need the underlying request object since restlib doesn't
    # have support for cookies yet.
    try:
        cookies = request.COOKIES
    except:
        cookies = {}
    if 'pysid' not in cookies:
        return (None, None)

    sid = cookies['pysid']

    try:
        session = Sessions.objects.get(sid=sid)
        d = cPickle.loads(str(session.data))
        username, password = d['_data']['authToken']
        if password == '':
            password = ValidPasswordToken
        return (username, password)
    except:
        pass
        
    return (None, None)
        
def getAuth(request):
    auth_header = {}
    if 'Authorization' in request.META:
        auth_header = {'Authorization': request.META['Authorization']}
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth_header =  {'Authorization': request.META['HTTP_AUTHORIZATION']}

    if 'Authorization' in auth_header:
        authType, user_pass = auth_header['Authorization'].split(' ', 1)
        if authType == 'Basic':
            try:
                user_name, password = base64.decodestring(user_pass
                        ).split(':', 1)
                return (user_name, password)
            except:
                pass
    else:
        return getCookieAuth(request)
        
    return (None, None)

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


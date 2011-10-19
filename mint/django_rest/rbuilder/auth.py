#
# Copyright (c) 2011 rPath, Inc.
#
from mint.django_rest.rbuilder.models import Sessions
from mint.django_rest.rbuilder.users.models import User
from mint.lib import auth_client
from hashlib import md5
import base64
import cPickle

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
    return user.getIsAdmin()

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
            user = User.objects.get(user_name=username)
        except User.DoesNotExist:
            return None
        if user.passwd and user.salt:
            salt = user.salt.decode('hex')
            m = md5(salt + password)
            if (m.hexdigest() == user.passwd):
                return user
        if mintConfig:
            client = auth_client.getClient(mintConfig.authSocket)
            if client.checkPassword(username, password):
                return user
        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


#
# Copyright (c) 2011 rPath, Inc.
#

from mint.django_rest.rbuilder.models import Users, UserGroups, Sessions
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
                username, password = base64.decodestring(user_pass
                        ).split(':', 1)
                return (username, password)
            except:
                pass
    else:
        return getCookieAuth(request)
        
    return (None, None)
    
def isAdmin(user):
     if user is not None and isinstance(user, Users):
         groups = user.groups.all()
         admingroup = UserGroups.objects.get(usergroup='MintAdmin')
         if admingroup in groups:
             return True
     return False
 
def isAuthenticated(user):
     if user is not None and isinstance(user, Users):
         return True
     return False

class rBuilderBackend:

    def authenticate(self, username=None, password=None):
        try:
       	    user = Users.objects.get(username=username)
            m = md5(user.salt + password)
            if (m.hexdigest() == user.passwd):
       	        return user
        except Users.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(pk=user_id)
        except Users.DoesNotExist:
            return None

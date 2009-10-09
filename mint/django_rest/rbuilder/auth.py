from models import Users
import md5
import base64

def getAuth(request):
    auth_header = {}
    if 'Authorization' in request.META:
        auth_header = {'Authorization': request.META['Authorization']}
    elif 'HTTP_AUTHORIZATION' in request.META:
        auth_header =  {'Authorization': request.META['HTTP_AUTHORIZATION']}

    if 'Authorization' in auth_header:
        type, user_pass = auth_header['Authorization'].split(' ', 1)

        try:
            username, password = base64.decodestring(user_pass).split(':', 1)
            return (username, password)
        except:
            pass

    return (None, None)

class rBuilderBackend:

    def authenticate(self, username=None, password=None):
        try:
       	    user = Users.objects.get(username=username)
            m = md5.new(user.salt + password)
            if (m.hexdigest() == user.passwd):
       	        return user
        except User.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return Users.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

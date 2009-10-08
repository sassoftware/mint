from api.models import Users
import md5

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

from mint.django_rest.rbuilder import service
from mint.django_rest.deco import requires, return_xml


class UserNoticesService(service.BaseService):

    @return_xml
    def rest_GET(self, request, user_id):
        return self.get(user_id)

    def get(self, user_id):
        return self.mgr.getUserNotices(user_id)

    @requires('user_notice')
    @return_xml
    def rest_POST(self, request, user_id, user_notice):
        return self.mgr.createUserNotice(user_id, user_notice)


class GlobalNoticesService(service.BaseService):
    
    @return_xml
    def rest_GET(self, request):
        return self.get()
        
    def get(self):
        return self.mgr.getGlobalNotices()
    
    @requires('global_notice')
    @return_xml
    def rest_POST(self, request, global_notice):
        return self.mgr.createGlobalNotice(global_notice)

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.notices import models

exposed = basemanager.exposed

class UserNoticesManager(basemanager.BaseManager):
    @exposed
    def getUserNotices(self, user_id):
        UserNotices = models.UserNotices()
        UserNotices.user_notice = models.UserNotice.objects.all().filter(user_id=user_id)
        return UserNotices
    
    @exposed
    def createUserNotice(self, user_notice):
        user_notice.save()
        return user_notice
    
    @exposed
    def deleteUserNotice(self, user_notice_id):
        user_notice = models.UserNotice.objects.get(pk=user_notice_id)
        user_notice.delete()
    
    
class GlobalNoticesManager(basemanager.BaseManager):
    @exposed
    def getGlobalNotices(self):
        GlobalNotices = models.GlobalNotices()
        GlobalNotices.global_notice = models.GlobalNotice.objects.all()
        return GlobalNotices
        
    @exposed
    def createGlobalNotice(self, global_notice):
        global_notice.save()
        return global_notice

    @exposed
    def deleteGlobalNotice(self, global_notice_id):
        global_notice = models.GlobalNotice.objects.get(pk=global_notice_id)
        global_notice.delete()
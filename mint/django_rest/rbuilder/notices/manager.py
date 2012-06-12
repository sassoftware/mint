#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.notices import models

exposed = basemanager.exposed

class UserNoticesManager(basemanager.BaseManager):
    @exposed
    def getUserNotices(self, user_id):
        UserNotices = models.UserNotices()
        UserNotices.user_notice = models.UserNotice.objects.all().filter(user_id=user_id)
        UserNotices.global_notice = models.GlobalNotice.objects.all()
        return UserNotices
    
    @exposed
    def createUserNotice(self, user_notice):
        user_notice.save()
        return user_notice
    
    @exposed
    def deleteUserNotice(self, user_notice_id):
        user_notice = models.UserNotice.objects.get(pk=user_notice_id)
        user_notice.delete()
#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

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
        return self.mgr.createUserNotice(user_notice)

    def rest_DELETE(self, request, user_id):
        self.mgr.deleteUserNotice(user_id)

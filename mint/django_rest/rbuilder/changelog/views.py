#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.deco import return_xml
from mint.django_rest.rbuilder import service

class BaseChangeLogService(service.BaseService):
    pass

class ChangeLogService(BaseChangeLogService):

    @return_xml
    def rest_GET(self, request, change_log_id=None):
        return self.get(change_log_id)

    def get(self, change_log_id):
        if change_log_id:
            return self.mgr.getChangeLog(change_log_id)
        else:
            return self.mgr.getChangeLogs()

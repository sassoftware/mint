#!/usr/bin/python
#
# Copyright (c) 2011 rPath, Inc.
#
# All rights reserved.
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.manager.basemanager import exposed
from mint.django_rest.rbuilder.changelog import models

class ChangeLogManager(basemanager.BaseManager):

    @exposed 
    def getChangeLogs(self):
        changeLogs = models.ChangeLogs()
        changeLogs.change_log = models.ChangeLog.objects.all()
        return changeLogs

    @exposed
    def getChangeLog(self, change_log_id):
        changeLog = models.ChangeLog.objects.get(pk=change_log_id)
        return changeLog

#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import weakref

from mint.django_rest.rbuilder.manager import basemanager

from mint.django_rest.rbuilder.inventory.manager import systemmgr
from mint.django_rest.rbuilder.inventory.manager import versionmgr
from mint.django_rest.rbuilder.inventory.manager import repeatermgr
from mint.django_rest.rbuilder.inventory.manager import jobmgr

class RbuilderManager(basemanager.BaseManager):
    def __init__(self, cfg=None, userName=None):
        super(self.__class__, self).__init__(cfg=cfg, userName=userName)
        self.sysMgr = systemmgr.SystemManager(weakref.proxy(self))
        self.versionMgr = versionmgr.VersionManager(weakref.proxy(self))
        self.repeaterMgr = repeatermgr.RepeaterManager(weakref.proxy(self))
        self.jobMgr = jobmgr.JobManager(weakref.proxy(self))

        # Methods we simply copy
        for subMgr in [ self.sysMgr, self.versionMgr, self.jobMgr ]:
            for objName in subMgr.__class__.__dict__:
                obj = getattr(subMgr, objName, None)
                if getattr(obj, 'exposed', None):
                    if hasattr(self, objName):
                        raise Exception("Conflict for method %s" % objName)
                    setattr(self, objName, obj)



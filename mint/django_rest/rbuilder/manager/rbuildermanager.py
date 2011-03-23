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

from mint.django_rest.rbuilder.querysets.manager import QuerySetManager
from mint.django_rest.rbuilder.packages.manager import PackageManager
from mint.django_rest.rbuilder.changelog.manager import ChangeLogManager
from mint.django_rest.rbuilder.projects.manager import ProjectManager
from mint.django_rest.rbuilder.packageworkspaces.manager import PackageWorkspaceManager

class RbuilderManager(basemanager.BaseRbuilderManager):

    MANAGERS = {
        'sysMgr' : systemmgr.SystemManager,
        'versionMgr' : versionmgr.VersionManager,
        'repeaterMgr' : repeatermgr.RepeaterManager,
        'jobMgr' : jobmgr.JobManager,
        'querySetMgr' : QuerySetManager,
        'packageMgr' : PackageManager,
        'changeLogMgr' : ChangeLogManager,
        'projectMgr' : ProjectManager,
        'packageWorkspaceMgr' : PackageWorkspaceManager,
    }

    def __init__(self, cfg=None, userName=None):
        super(self.__class__, self).__init__(cfg=cfg, userName=userName)
        for name, manager in self.MANAGERS.items():
            mgr = manager(weakref.proxy(self))
            setattr(self, name, mgr)
            self.managers.append(mgr)

        # Methods we simply copy
        for subMgr in self.managers:
            for objName in subMgr.__class__.__dict__:
                obj = getattr(subMgr, objName, None)
                if getattr(obj, 'exposed', None):
                    if hasattr(self, objName):
                        raise Exception("Conflict for method %s" % objName)
                    setattr(self, objName, obj)

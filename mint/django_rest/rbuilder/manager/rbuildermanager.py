#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import weakref

from mint.django_rest.rbuilder.manager import basemanager

from mint.django_rest.rbuilder.inventory.manager.systemmgr import SystemManager
from mint.django_rest.rbuilder.inventory.manager.versionmgr import VersionManager
from mint.django_rest.rbuilder.inventory.manager.repeatermgr import RepeaterManager
from mint.django_rest.rbuilder.inventory.manager.jobmgr import JobManager
from mint.django_rest.rbuilder.querysets.manager import QuerySetManager
from mint.django_rest.rbuilder.changelog.manager import ChangeLogManager
from mint.django_rest.rbuilder.packages.manager import PackageManager, PackageVersionManager
from mint.django_rest.rbuilder.users.manager import UsersManager, UserGroupsManager, UserGroupMembersManager, UserUserGroupsManager
from mint.django_rest.rbuilder.notices.manager import UserNoticesManager, GlobalNoticesManager

class RbuilderManager(basemanager.BaseRbuilderManager):

    MANAGERS = {
        'sysMgr' : SystemManager,
        'versionMgr' : VersionManager,
        'repeaterMgr' : RepeaterManager,
        'jobMgr' : JobManager,
        'querySetMgr' : QuerySetManager,
        'changeLogMgr' : ChangeLogManager,
        'packageMgr' : PackageManager,
        'packageVersionMgr' : PackageVersionManager,
        'usersMgr' : UsersManager,
        'userGroupsMgr': UserGroupsManager,
        'userGroupMembersMgr': UserGroupMembersManager,
        'userNoticesManager' : UserNoticesManager,
        'globalNoticesManager' : GlobalNoticesManager,
        'userUserGroupsManager' : UserUserGroupsManager,
    }

    def __init__(self, cfg=None, userName=None):
        super(RbuilderManager, self).__init__(cfg=cfg, userName=userName)
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

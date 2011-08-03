#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

import weakref

from mint.django_rest.rbuilder.manager import basemanager

from mint.django_rest.rbuilder.discovery.manager import DiscoveryManager
from mint.django_rest.rbuilder.inventory.manager.systemmgr import SystemManager
from mint.django_rest.rbuilder.inventory.manager.versionmgr import VersionManager
from mint.django_rest.rbuilder.inventory.manager.repeatermgr import RepeaterManager
from mint.django_rest.rbuilder.jobs.manager import JobManager
from mint.django_rest.rbuilder.querysets.manager import QuerySetManager
from mint.django_rest.rbuilder.changelog.manager import ChangeLogManager
from mint.django_rest.rbuilder.packageindex.manager import PackageManager
from mint.django_rest.rbuilder.projects.manager import ProjectManager
from mint.django_rest.rbuilder.users.manager import UsersManager, UserGroupsManager, UserGroupMembersManager, UserUserGroupsManager
from mint.django_rest.rbuilder.notices.manager import UserNoticesManager
from mint.django_rest.rbuilder.modulehooks.manager import ModuleHooksManager
from mint.django_rest.rbuilder.platforms.manager import SourceStatusManager, \
                                                        SourceErrorsManager, \
                                                        SourceManager, \
                                                        SourceTypeDescriptorManager, \
                                                        SourceTypeStatusTestManager, \
                                                        SourceTypeManager, \
                                                        PlatformLoadStatusManager, \
                                                        PlatformSourceManager, \
                                                        PlatformSourceTypeManager, \
                                                        PlatformImageTypeManager, \
                                                        PlatformLoadManager, \
                                                        PlatformVersionManager, \
                                                        PlatformManager
from mint.django_rest.rbuilder.repos.manager import ReposManager

class RbuilderManager(basemanager.BaseRbuilderManager):

    MANAGERS = {
        'discMgr' : DiscoveryManager,
        'sysMgr' : SystemManager,
        'versionMgr' : VersionManager,
        'repeaterMgr' : RepeaterManager,
        'jobMgr' : JobManager,
        'querySetMgr' : QuerySetManager,
        'changeLogMgr' : ChangeLogManager,
        'packageMgr' : PackageManager,
        'usersMgr' : UsersManager,
        'userGroupsMgr': UserGroupsManager,
        'userGroupMembersMgr': UserGroupMembersManager,
        'projectManager' : ProjectManager,
        'userNoticesMgr' : UserNoticesManager,
        'userUserGroupsManager' : UserUserGroupsManager,
        'sourceStatusMgr' : SourceStatusManager,
        'sourceErrorsMgr' : SourceErrorsManager,
        'sourceMgr' : SourceManager,
        'sourceTypeDescriptorMgr': SourceTypeDescriptorManager,
        'sourceTypeStatusTestMgr' : SourceTypeStatusTestManager,
        'sourceTypeMgr' : SourceTypeManager,
        'platformStatusMgr' : PlatformLoadStatusManager,
        'platformSourceMgr' : PlatformSourceManager,
        'platformSourceTypeMgr' : PlatformSourceTypeManager,
        'platformImageTypeMgr' : PlatformImageTypeManager,
        'platformLoadMgr' : PlatformLoadManager,
        'platformVersionMgr' : PlatformVersionManager,
        'platformMgr' : PlatformManager,
        'modulehooksMgr' : ModuleHooksManager,
        'reposMgr' : ReposManager,
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

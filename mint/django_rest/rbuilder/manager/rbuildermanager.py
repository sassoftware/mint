#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import weakref

from django.db import connection, transaction
from mint.django_rest.rbuilder.manager import basemanager

from mint.django_rest.rbuilder.discovery.manager import DiscoveryManager
from mint.django_rest.rbuilder.inventory.manager.systemmgr import SystemManager
from mint.django_rest.rbuilder.inventory.manager.repeatermgr import RepeaterManager
from mint.django_rest.rbuilder.jobs.manager import JobManager
from mint.django_rest.rbuilder.querysets.manager import QuerySetManager
from mint.django_rest.rbuilder.packageindex.manager import PackageManager
from mint.django_rest.rbuilder.projects.manager import ProjectManager
from mint.django_rest.rbuilder.users.manager import UsersManager
from mint.django_rest.rbuilder.modulehooks.manager import ModuleHooksManager
from mint.django_rest.rbuilder.platforms.manager import PlatformImageTypeManager, \
                                                        PlatformVersionManager, \
                                                        PlatformManager
from mint.django_rest.rbuilder.repos.manager import ReposManager
from mint.django_rest.rbuilder.rbac.manager.rbacmanager import RbacManager
from mint.django_rest.rbuilder.targets.manager import TargetsManager,\
                                                      TargetTypesManager,\
                                                      TargetTypeJobsManager,\
                                                      TargetJobsManager
from mint.django_rest.rbuilder.images.manager.imagesmanager import ImagesManager

class RbuilderManager(basemanager.BaseRbuilderManager):

    MANAGERS = {
        'discMgr' : DiscoveryManager,
        'sysMgr' : SystemManager,
        'repeaterMgr' : RepeaterManager,
        'jobMgr' : JobManager,
        'querySetMgr' : QuerySetManager,
        'packageMgr' : PackageManager,
        'usersMgr' : UsersManager,
        'projectManager' : ProjectManager,
        'platformImageTypeMgr' : PlatformImageTypeManager,
        'platformVersionMgr' : PlatformVersionManager,
        'platformMgr' : PlatformManager,
        'modulehooksMgr' : ModuleHooksManager,
        'reposMgr' : ReposManager,
        'rbacMgr' : RbacManager,
        'targetsManager' : TargetsManager,
        'targetTypesManager': TargetTypesManager,
        'targetTypeJobsManager' : TargetTypeJobsManager,
        'targetJobsManager' : TargetJobsManager,
        'imagesManager' : ImagesManager,
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

    def enterTransactionManagement(self):
        transaction.enter_transaction_management()
        transaction.managed(True)

    def leaveTransactionManagement(self):
        transaction.leave_transaction_management()

    def commit(self):
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.leave_transaction_management()
            transaction.enter_transaction_management(managed=True)
            return
        connection.commit_unless_managed()

    def rollback(self):
        if transaction.is_managed():
            transaction.rollback()
            return
        connection.rollback_unless_managed()

    def prepareAutocommit(self):
        # Commit and leave transaction management
        if transaction.is_managed():
            if transaction.is_dirty():
                transaction.commit()
            transaction.managed(False)
            transaction.leave_transaction_management()
            return
        connection.commit_unless_managed()

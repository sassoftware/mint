#
# Copyright (c) 2011 rPath, Inc.
#
# All Rights Reserved
#

from mint.django_rest.rbuilder.manager import basemanager
from mint.django_rest.rbuilder.modulehooks import models as modulehooksModels
import os
import fnmatch


exposed = basemanager.exposed


class ModuleHooksManager(basemanager.BaseManager):
    @exposed
    def getModuleHooks(self):
        ModuleHooks = modulehooksModels.ModuleHooks()
        ModuleHooks.module_hook = []
        for path, dirs, files in os.walk(self.mgr.cfg.moduleHooksDir):
            for filename in files:
                if fnmatch.fnmatch(filename, self.mgr.cfg.moduleHooksExt):
                    joined = os.path.join('hooks', filename)
                    ModuleHooks.module_hook.append(modulehooksModels.ModuleHook(url=joined))
        return ModuleHooks

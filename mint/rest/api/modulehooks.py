#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import fnmatch
import os

from restlib import response
from mint.rest.api import base
from mint.rest.api import models

from mint.rest.middleware import auth

class ModuleController(base.BaseController):
    modelName = 'modules'

    @auth.public
    def index(self, request):
        moduleHooksList = models.ModuleHooks()
        for path, dirs, files in os.walk(self.cfg.moduleHooksDir):
            for file in [filename for filename in files 
                    if fnmatch.fnmatch (filename, self.cfg.moduleHooksExt)]:

                moduleHooksList.moduleHooks.append(
                    models.ModuleHook( os.path.join('hooks',file)))
        return moduleHooksList


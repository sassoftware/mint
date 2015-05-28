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
        moduleHooksList.moduleHooks.sort()
        return moduleHooksList

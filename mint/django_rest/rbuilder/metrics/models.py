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


import sys
from xobj import xobj
from mint.django_rest.rbuilder import modellib
from django.db import models
from debug_toolbar.panels import version, timer

class Metrics(modellib.XObjModel):

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(tag='metrics')

    server_versions = modellib.XObjModel()
    timer = modellib.XObjModel

    def serialize(self, request=None):
        self.server_versions = self.server_versions.serialize(request)
        self.timer = self.timer.serialize(request)
        return self

class ServerVersions(modellib.XObjModel):

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
        tag='server_versions')

    panel = version.VersionDebugPanel

    django_version = models.TextField()
    debug_toolbar_version = models.TextField()

    def __init__(self, context):
        modellib.XObjModel.__init__(self)
        self.django_version = context['versions']['Django']
        self.debug_toolbar_version = context['versions']['Debug toolbar']

class Timer(modellib.XObjModel):

    class Meta:
        abstract = True

    _xobj = xobj.XObjMetadata(
        tag='timer')

    panel = timer.TimerDebugPanel

    user_cpu_time = models.TextField()
    system_cpu_time = models.TextField()
    total_cpu_time = models.TextField()
    elapsed_time = models.TextField()
    context_switches = models.TextField()

    def __init__(self, context):
        modellib.XObjModel.__init__(self)
        rows = context['rows']
        for r in rows:
            setattr(self, r[0].lower().replace(' ', '_'), r[1])

panelModels = {}
for mod_obj in sys.modules[__name__].__dict__.values():
    if hasattr(mod_obj, 'panel'):
        if mod_obj.panel:
            panelModels.update({mod_obj.panel:mod_obj})

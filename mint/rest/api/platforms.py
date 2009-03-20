#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models

class PlatformController(base.BaseController):
    # TODO: someday have a way to enable disable platforms 
    def index(self, request):
        return self.db.listPlatforms()

#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

from mint.rest.api import base
from mint.rest.api import models

from mint.rest.middleware import auth

class PlatformController(base.BaseController):
    @auth.public
    def index(self, request):
        return self.db.listPlatforms()

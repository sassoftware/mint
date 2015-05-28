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


import logging
from django.db import transaction

from mint import config
from mint.db import database
from mint.django_rest.rbuilder.users import models as usersmodels
from mint.lib.mintutils import cached_property
from mint.rest.db.database import Database as RestDatabase

log = logging.getLogger(__name__)

def exposed(fn):
    fn.exposed = True
    return fn

# Shortcut for django decorator
autocommit = transaction.autocommit
commitOnSuccess = transaction.commit_on_success

class BaseManager(object):
    def __init__(self, mgr):
        # mgr is a weakref to avoid circular references. Access its fields
        # through properties
        self.mgr = mgr

    @property
    def cfg(self):
        return self.mgr.cfg

    @property
    def restDb(self):
        return self.mgr.restDb

    @property
    def user(self):
        return self.mgr.user

    @property
    def auth(self):
        return self.mgr._auth

class BaseRbuilderManager(object):

    MANAGERS = {}

    def __init__(self, cfg=None, userName=None):
        if cfg:
            self.cfg = cfg
        self._auth = None
        self.managers = []
        if userName is None:
            self.user = None
        else:
            self.user = usersmodels.User.objects.get(user_name=userName)

    @cached_property
    def cfg(self):
        # NOTE: this path should only be used in the testsuite. Normally
        # mint.web.wsgi_hook should be the only place MintConfig is ever
        # instantiated.
        cfgPath = config.RBUILDER_CONFIG
        return config.getConfig(cfgPath)

    @cached_property
    def restDb(self):
        # NOTE: this path should only be used in the testsuite. Normally
        # mint.web.wsgi_hook should be the only place Database is ever
        # instantiated.
        return self._makeRestDb(self.cfg)

    def _makeRestDb(self, cfg, db=None):
        mintDb = database.Database(cfg, db)
        restDb = RestDatabase(cfg, mintDb, dbOnly=True)
        return restDb

    def setAuth(self, request, auth, user):
        self._auth = auth
        self.user = user

        context = request.META['mint.wsgiContext']
        self.restDb = self._makeRestDb(context.cfg, context.db)
        self.restDb.setAuth(auth, auth.getToken())

    def close(self):
        if self.restDb is not None:
            self.restDb.close()
            self.restDb = None

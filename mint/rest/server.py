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

from restlib.http import wsgi

from mint.db import database
from mint.rest.api import site
from mint.rest.db import database as restDatabase
from mint.rest.middleware import auth
from mint.rest.middleware import error
from mint.rest.middleware import formatter


def restHandler(context):
    mintDb = database.Database(context.cfg, db=context.db)
    restDb = restDatabase.Database(context.cfg, mintDb)
    controller = site.RbuilderRestServer(context.cfg, restDb)
    handler = wsgi.WSGIHandler(controller)
    handler.addCallback(auth.AuthenticationCallback(context.cfg, restDb,
        controller, context.authToken))
    handler.addCallback(formatter.FormatCallback(controller))
    handler.addCallback(error.ErrorCallback(controller))
    return handler.handle(context.req, pathPrefix=context.req.script_name)

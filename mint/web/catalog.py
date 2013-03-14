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

from mint.db import database
from restlib.http import wsgi
from catalogService import handler as catalog_handler
from catalogService.rest.database import RestDatabase


def catalogHandler(context):
    mintDb = database.Database(context.cfg, db=context.db)
    catalogDb = RestDatabase(context.cfg, mintDb)
    handler = catalog_handler.getHandler(catalogDb, wsgi.WSGIHandler)
    return handler.handle(context.req, pathPrefix=context.req.script_name)

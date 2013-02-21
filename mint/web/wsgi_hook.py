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
import sys
import webob
from conary import dbstore
from conary.lib import coveragehook
from webob import exc as web_exc

from mint import config
from mint.db.repository import RepositoryManager
from mint.lib import mintutils
from mint.logerror import logWebErrorAndEmail
from mint.rest.api import site as rest_site
from mint.rest.server import restHandler
from mint.web import app
from mint.web import rpchooks
from mint.web.catalog import catalogHandler
from mint.web.hooks.conaryhooks import conaryHandler
from mint.web.webhandler import normPath, setCacheControl, HttpError
log = logging.getLogger(__name__)


class application(object):
    requestFactory = webob.Request
    responseFactory = webob.Response

    environ = None
    cfg = None
    req = None
    db = None
    rm = None
    iterable = None

    def __init__(self, environ, start_response):
        coveragehook.install()
        mintutils.setupLogging(consoleLevel=logging.INFO, consoleFormat='apache')
        self.environ = environ
        try:
            self.req = self.requestFactory(environ)
        except:
            log.exception("Error parsing request:")
            response = web_exc.HTTPBadRequest()
            self.iterable = response(environ, start_response)
            return
        if not self.cfg:
            # Cache config in the class
            type(self).cfg = config.getConfig()

        try:
            response = self.handleRequest()
        except web_exc.HTTPException, exc:
            response = exc
        except:
            exc_info = sys.exc_info()
            logWebErrorAndEmail(self.req, self.cfg, *exc_info)
            response = web_exc.HTTPInternalServerError(explanation=
                    "Something has gone terribly wrong. "
                    "Check the webserver logs for details.")
        finally:
            if self.rm:
                self.rm.close()
            if self.db:
                self.db.close()
            coveragehook.save()
            logging.shutdown()
        if callable(response):
            self.iterable = response(environ, start_response)
        else:
            self.iterable = response

    def __iter__(self):
        return iter(self.iterable)

    def handleRequest(self):
        self.db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        self.rm = RepositoryManager(self.cfg, self.db)

        # Proxied Conary requests can have all sorts of paths, so look for a
        # header instead.
        if 'x-conary-servername' in self.req.headers:
            return self.handleConary()

        elem = self.req.path_info_peek()
        if elem in ('changeset', 'conary', 'repos'):
            return self.handleConary()
        elif elem in ('xmlrpc', 'xmlrpc-private', 'jsonrpc'):
            return rpchooks.rpcHandler(self)
        elif elem == 'api':
            return self.handleApi()
        elif elem == 'catalog':
            return self.handleCatalog()
        else:
            return self.handleWeb()

    def handleApi(self):
        self.req.path_info_pop()
        if self.req.path_info_peek() in rest_site.RbuilderRestServer.urls:
            # "restlib" API
            return restHandler(self)
        else:
            # django API
            pass

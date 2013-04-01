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
import os
import sys
import webob
from beaker import session
from conary import dbstore
from conary.lib import coveragehook
from conary.repository.netrepos import netauth
from conary.repository.netrepos import netserver
from django.core.handlers import wsgi as djwsgi
from webob import exc as web_exc

from mint import config
from mint.db.repository import RepositoryManager
from mint.lib import mintutils
from mint.logerror import logWebErrorAndEmail
from mint.rest.api import site as rest_site
from mint.rest.server import restHandler
from mint.web import app
from mint.web import catalog
from mint.web import conaryhooks
from mint.web import rpchooks
from mint.web import uploader
from mint.web import webhandler
log = logging.getLogger(__name__)


class application(object):
    requestFactory = webob.Request
    responseFactory = webob.Response

    authToken = None
    cfg = None
    db = None
    environ = None
    iterable = None
    req = None
    rm = None
    session = None
    start_response = None

    def __init__(self, environ, start_response):
        coveragehook.install()
        mintutils.setupLogging(consoleLevel=logging.INFO, consoleFormat='apache')
        # gunicorn likes to umask(0) when daemonizing, so put back something
        # reasonable if that's the case.
        oldUmask = os.umask(022)
        if oldUmask != 0:
            os.umask(oldUmask)
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
        self.session = session.SessionObject(environ,
                invalidate_corrupt=True,
                type='file',
                data_dir=self.cfg.getSessionDir(),
                key='pysid',
                secure=True,
                httponly=True,
                )

        self.start_response = start_response
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
            self._persistSession(response)
            self.iterable = response(environ, start_response)
        else:
            self.iterable = response

    def __iter__(self):
        return iter(self.iterable)

    def handleRequest(self):
        self.db = dbstore.connect(self.cfg.dbPath, self.cfg.dbDriver)
        self.rm = RepositoryManager(self.cfg, self.db,
                baseUrl=self.req.application_url)
        self.authToken = self._getAuth()
        self.authToken = netserver.AuthToken(*self.authToken)
        self.authToken.remote_ip = self.req.client_addr
        self.req.environ['mint.authToken'] = self.authToken

        if '_method' in self.req.GET:
            method = self.req.GET['_method'].upper()
            allowed = ['GET', 'PUT', 'POST', 'DELETE', 'HEAD']
            if method not in allowed:
                return web_exc.HTTPMethodNotAllowed(allow=allowed)
            self.req.method = method

        # Proxied Conary requests can have all sorts of paths, so look for a
        # header instead.
        if 'x-conary-servername' in self.req.headers:
            return conaryhooks.conaryHandler(self)

        elem = self.req.path_info_peek()
        if elem in ('changeset', 'conary', 'repos'):
            return conaryhooks.conaryHandler(self)
        elif elem in ('xmlrpc', 'xmlrpc-private', 'jsonrpc'):
            return rpchooks.rpcHandler(self)
        elif elem == 'api':
            return self.handleApi()
        elif elem == 'catalog':
            self.req.path_info_pop()
            return catalog.catalogHandler(self)
        elif elem == 'cgi-bin':
            self.req.path_info_pop()
            return uploader.handle(self)
        else:
            return self.handleWeb()

    def handleApi(self):
        script_name, path_info = self.req.script_name, self.req.path_info
        self.req.path_info_pop()
        if self.req.path_info_peek() in rest_site.RbuilderRestServer.urls:
            # "restlib" API
            return restHandler(self)
        # django API
        os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                'mint.django_rest.settings')
        self.req.script_name, self.req.path_info = script_name, path_info
        return djwsgi.WSGIHandler()(self.req.environ, self.start_response)

    def handleWeb(self):
        webfe = app.MintApp(self.req, self.cfg,
                db=self.db,
                session=self.session,
                authToken=self.authToken,
                reposShim=self.rm,
                )
        return webfe._handle()

    def _getAuth(self):
        authToken = webhandler.getHttpAuth(self.req)
        if not isinstance(authToken, basestring):
            return authToken[:2]
        if authToken != self.session.id:
            self.session.id = authToken
            self.session.load()
        authToken = self.session.get('authToken', None)
        if not authToken:
            return ()
        if authToken[1] == '':
            # Pre-authenticated session
            return (authToken[0], netauth.ValidPasswordToken)
        # Discard old password-containing sessions to force a fresh login
        return ()

    def _persistSession(self, response):
        session = self.session
        if not session.accessed():
            return
        session.persist()
        headers = session.__dict__['_headers']
        if not headers['set_cookie']:
            return
        cookie = headers['cookie_out']
        if cookie:
            response.headers.add('Set-Cookie', cookie)

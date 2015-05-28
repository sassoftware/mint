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


import kid
import sys
import time
import webob
from webob import exc as web_exc

from mint import shimclient
from mint import userlevels
from mint.helperfuncs import getProjectText, weak_signature_call
from mint.mint_error import MintError
from mint.web import fields
from mint.web.admin import AdminHandler
from mint.web.site import SiteHandler
from mint.web.webhandler import WebHandler, normPath


# called from hooks.py if an exception was not caught
class ErrorHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        return self.errorPage

    def errorPage(self, *args, **kwargs):
        return self._write('error', error = ' An unknown error occurred while handling your request. Site maintainers have been notified.')


class MintApp(WebHandler):
    project = None
    userLevel = userlevels.NONMEMBER
    user = None
    responseFactory = webob.Response

    def __init__(self, req, cfg, repServer = None, db=None, session=None,
            authToken=None, reposShim=None):
        self.req = req
        self.cfg = cfg
        self.db = db
        self.reposShim = reposShim

        # always send html-strict; xhtml FTL
        # The default behavior of kid changed between 0.9.1 and 0.9.6
        # in 0.9.1 html-strict produced upper case tags and HTML-strict did not
        # exist. in 0.9.6 HTML-strict produces upper case tags and html-strict
        # produces lower case tags. we want upper case tags.
        if 'HTML-strict' in kid.output_methods:
            self.output = 'HTML-strict'
        else:
            self.output = 'html-strict'
        self.content_type = 'text/html; charset=utf-8'
        self.response = self.responseFactory(content_type=self.content_type)

        self.fields = req.params.mixed()
        self.basePath = normPath(req.script_name)
        if session is None:
            session = {}
        self.session = session
        self.authToken = authToken

        self.siteHandler = SiteHandler()
        self.adminHandler = AdminHandler()
        self.errorHandler = ErrorHandler()

    def _handle(self):
        method = self.req.method.upper()
        allowed = ['GET', 'POST', 'PUT']
        if method not in allowed:
            return web_exc.HTTPMethodNotAllowed(allow=allowed)

        if not self.authToken:
            self.authToken = ('anonymous', 'anonymous')

        # open up a new client with the retrieved authToken
        self.client = shimclient.ShimMintClient(self.cfg, self.authToken,
                self.db)

        self.auth = self.client.checkAuth()

        if self.auth.authorized:
            self.user = self.client.getUser(self.auth.userId)
        self.auth.setToken(self.authToken)

        method = self._getHandler()

        d = self.fields.copy()
        d['auth'] = self.auth

        def logTraceback():
            import traceback
            e_type, e_value, e_tb = sys.exc_info()

            formatted = ''.join(traceback.format_exception(
                e_type, e_value, e_tb))
            return formatted

        try:
            output = weak_signature_call(method, **d)
        except MintError, e:
            tb = logTraceback()
            err_name = sys.exc_info()[0].__name__
            output = self._write("error", shortError = err_name, error = str(e),
                traceback = self.cfg.debugMode and tb or None)
        except fields.MissingParameterError, e:
            tb = logTraceback()
            output = self._write("error", shortError = "Missing Parameter", error = str(e))
        except fields.BadParameterError, e:
            tb = logTraceback()
            output = self._write("error", shortError = "Bad Parameter", error = str(e),
                traceback = self.cfg.debugMode and tb or None)
        else:
            self.response.last_modified = time.time()
        self.response.body = output
        self._clearAllMessages()
        return self.response

    def _getHandler(self):
        self.baseUrl = self.req.application_url + '/'
        self.httpsUrl = self.req.application_url.replace('http://', 'https://') + '/'
        self.hostName = self.req.host.rsplit(':', 1)[0]
        self.SITE = self.req.host + '/'
        self.siteHost = self.cfg.siteHost
        self.isOwner = self.userLevel == userlevels.OWNER or self.auth.admin

        # Handle messages stashed in the session
        self.infoMsg = self.session.setdefault('infoMsg', '')
        self.searchType = self.session.setdefault('searchType', getProjectText().title()+"s")
        self.searchTerms = ''
        self.errorMsgList = self._getErrors()

        # a set of information to be passed into the next handler
        context = {
            'auth':             self.auth,
            'authToken':        self.auth.getToken(),
            'client':           self.client,
            'cfg':              self.cfg,
            'db':               self.db,
            'fields':           self.fields,
            'req':              self.req,
            'response':         self.response,
            'session':          self.session,
            'siteHost':         self.cfg.siteHost,
            'searchType':       self.searchType,
            'searchTerms':      '',
            'toUrl':            self.req.url,
            'baseUrl':          self.baseUrl,
            'basePath':         self.basePath,
            'httpsUrl':         self.httpsUrl,
            'hostName':         self.hostName,
            'project':          None,
            'SITE':             self.SITE,
            'userLevel':        self.userLevel,
            'user':             self.user,
            'isOwner':          self.isOwner,
            'infoMsg':          self.infoMsg,
            'errorMsgList':     self.errorMsgList,
            'output':           self.output,
            'remoteIp':         self.req.client_addr,
            'reposShim':        self.reposShim,
        }

        # match the requested url to the right url handler
        for match, urlHandler in [
                ('admin', self.adminHandler),
                ('administer', self.adminHandler),
                ('unknownError', self.errorHandler),
                ]:
            if self.req.path_info_peek() == match:
                self.req.path_info_pop()
                break
        else:
            urlHandler = self.siteHandler
        context['cmd'] = self.req.path_info
        return urlHandler.handle(context)

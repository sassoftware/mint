#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import base64
import os
import sys
import re
import time
from urllib import quote, unquote

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

from conary.web import fields

from mint.session import SqlSession, COOKIE_NAME
from mint import database
from mint import mint_error
from mint import mint_server
from mint import shimclient
from mint import users, userlevels

from admin import AdminHandler
from project import ProjectHandler
from site import SiteHandler
from repos import ConaryHandler
from setup import SetupHandler
import cache

from webhandler import WebHandler, normPath, HttpNotFound
from cache import pageCache, reqHash

#called from hooks.py if an exception was not caught
class ErrorHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        return self.errorPage

    def errorPage(self, *args, **kwargs):
        return self._write('error', error = ' An unknown error occured while handling your request. Site maintainers have been notified.')

shimClients = {}

class MintApp(WebHandler):
    project = None
    projectList = []
    projectDict = {}
    userLevel = userlevels.NONMEMBER
    user = None
    session = {}

    def __init__(self, req, cfg, repServer = None):
        self.req = req
        self.cfg = cfg

        # always send xhtml-strict
        self.output = 'xhtml-strict'

        # Send the proper content type for those browser who know to ask
        # for XHTML. Otherwise, serve XHTML as text/html with the proper
        # charset encoding as per the W3C guidelines
        # (c.f. http://www.w3.org/TR/xhtml1/guidelines.html)
        if 'application/xhtml+xml' in self.req.headers_in.get('Accept', ''):
            self.content_type = 'application/xhtml+xml'
        else:
            self.content_type = 'text/html; charset=utf-8'

        self.req.content_type = self.content_type

        try:
            self.fields = dict(FieldStorage(self.req))
        # for some reason mod_python raises a 501 error
        # when it fails to parse a POST request. raise
        # a 404 instead.
        except apache.SERVER_RETURN:
            raise HttpNotFound

        self.basePath = normPath(self.cfg.basePath)

        self.siteHandler = SiteHandler()
        self.projectHandler = ProjectHandler()
        self.adminHandler = AdminHandler()
        self.errorHandler = ErrorHandler()
        self.setupHandler = SetupHandler()
        self.conaryHandler = ConaryHandler(req, cfg, repServer)

    def _handle(self, pathInfo):
        method = self.req.method.upper()
        if method not in ('GET', 'POST'):
            return apache.HTTP_METHOD_NOT_ALLOWED

        anonToken = ('anonymous', 'anonymous')

        if self.cfg.cookieSecretKey:
            cookies = Cookie.get_cookies(self.req, Cookie.SignedCookie, secret = self.cfg.cookieSecretKey)
        else:
            cookies = Cookie.get_cookies(self.req, Cookie.Cookie)

        sid = self.fields.get('sid', None)
        rememberMe = self.fields.get('rememberMe', False)
        if sid:
            self._session_start()
            if rememberMe != self.session.get('rememberMe', False):
                self.session['rememberMe'] = rememberMe
                self.session.save()
            self._redirect_storm(sid)

        if 'pysid' not in cookies:
            rh = cache.reqHash(self.req)
            if rh in cache.pageCache:
                self.req.write(cache.pageCache[rh])
                return apache.OK
        else:
            self._session_start()

        # default to anonToken if the current session has no authToken
        self.authToken = self.session.get('authToken', anonToken)

        # open up a new client with the retrieved authToken

        # XXX short-circuit this cache until we can determine if it's completely
        # safe in production:
        if True or self.authToken not in shimClients:
            shimClients[self.authToken] = shimclient.ShimMintClient(self.cfg, self.authToken)
        self.client = shimClients[self.authToken]

        self.auth = self.client.checkAuth()
        if self.auth.authorized:
            self.user = self.client.getUser(self.auth.userId)
            self.projectList = self.client.getProjectsByMember(self.auth.userId)
            self.projectDict = {}
            for project, level in self.projectList:
                l = self.projectDict.setdefault(level, [])
                l.append(project)

        self.auth.setToken(self.authToken)

        method = self._getHandler(pathInfo)

        d = self.fields.copy()
        d['auth'] = self.auth

        try:
            output = method(**d)
            if self.auth.authorized:
                self.session.save()
            elif 'cacheable' in method.__dict__:
                pageCache[reqHash(self.req)] = output

        except mint_error.MintError, e:
            import traceback
            tb = traceback.format_exc()

            for line in tb.split("\n"):
                self.req.log_error(line)

            self.toUrl = self.cfg.basePath
            err_name = sys.exc_info()[0].__name__
            output = self._write("error", shortError = err_name, error = str(e),
                traceback = self.cfg.debugMode and tb or None)
        except fields.MissingParameterError, e:
            output = self._write("error", shortError = "Missing Parameter", error = str(e))

        self.req.write(output)
        return apache.OK

    def _getHandler(self, pathInfo):
        fullHost = self.req.headers_in.get('host', self.req.hostname)
        protocol='https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol='http'
        self.toUrl = ("%s://%s" % (protocol, fullHost)) + self.req.unparsed_uri
        dots = fullHost.split('.')
        hostname = dots[0]

        # if it looks like we're requesting a project (hostname isn't in reserved hosts
        # and doesn't match cfg.hostName, try to request the project.
        if hostname not in mint_server.reservedHosts \
            and hostname != self.cfg.hostName \
            and self.cfg.configured:
            try:
                project = self.client.getProjectByHostname(hostname)
            except Exception, e:
                self.req.log_error(str(e))
                raise HttpNotFound
            else:
                # coerce "external" projects to the externalSiteHost, or
                # internal projects to projectSiteHost.
                if project.external: # "external" projects are endorsed by us, so use siteHost
                    self._redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.externalSiteHost, self.cfg.basePath, hostname))
                else:
                    self._redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.projectSiteHost, self.cfg.basePath, hostname))

        self.siteHost = self.cfg.siteHost

        # redirect from domain.org to host.domain.org
        if self.cfg.hostName and fullHost == self.cfg.siteDomainName:
            self._redirect('http://' + self.cfg.hostName + "." + self.cfg.siteDomainName)

        # mapping of url regexps to handlers
        urls = (
            (r'^/project/',     self.projectHandler),
            (r'^/administer/',  self.adminHandler),
            (r'^/repos/',       self.conaryHandler),
            (r'^/setup/',       self.setupHandler),
            (r'^/unknownError', self.errorHandler),
            (r'^/',             self.siteHandler),
        )

        self.SITE = self.siteHost + self.basePath
        self.isOwner = self.userLevel == userlevels.OWNER or self.auth.admin

        if self.session.has_key('groupTroveId') and self.auth.authorized:
            try:
                self.groupTrove = self.client.getGroupTrove(self.session['groupTroveId'])
            except database.ItemNotFound:
                del self.session['groupTroveId']
                self.groupTrove = None
                self.groupProject = None
            else:
                self.groupProject = self.client.getProject(self.groupTrove.projectId)
        else:
            self.groupTrove = None
            self.groupProject = None

        # a set of information to be passed into the next handler
        context = {
            'auth':             self.auth,
            'authToken':        self.auth.getToken(),
            'client':           self.client,
            'cfg':              self.cfg,
            'fields':           self.fields,
            'projectList':      self.projectList,
            'projectDict':      self.projectDict,
            'req':              self.req,
            'session':          self.session,
            'siteHost':         self.cfg.siteHost,
            'toUrl':            self.toUrl,
            'basePath':         self.basePath,
            'project':          None,
            'SITE':             self.SITE,
            'userLevel':        self.userLevel,
            'user':             self.user,
            'isOwner':          self.isOwner,
            'groupTrove':       self.groupTrove,
            'groupProject':     self.groupProject,
            'output':           self.output,
        }

        if self.auth.stagnant and ''.join(pathInfo.split('/')) not in ['editUserSettings','confirm','logout']:
            context['cmd'] = 'confirmEmail'
            return self.siteHandler.handle(context)

        # match the requested url to the right url handler
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                urlHandler.content_type=self.content_type
                urlHandler.output = self.output
                context['cmd'] = pathInfo[len(match)-1:]
                ret = urlHandler.handle(context)
                return ret

        # fell through, nothing matched
        raise HttpNotFound

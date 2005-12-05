#
# Copyright (c) 2005 rPath, Inc.
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
from cookie_http import ConaryHandler
import cache

from webhandler import WebHandler, normPath 
from cache import pageCache, reqHash

# hack to set the default encoding to utf-8
# to overcome a kid bug.
reload(sys)
sys.setdefaultencoding("utf-8")

#called from hooks.py if an exception was not caught
class ErrorHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        return self.errorPage

    def errorPage(self, *args, **kwargs):
        self._write('error', error = ' An unknown error occured while handling your request. Site maintainers have been notified.')
        return apache.OK

class MintApp(WebHandler):
    project = None
    projectList = []
    userLevel = userlevels.NONMEMBER
    user = None
    session = {} 

    def __init__(self, req, cfg, repServer = None):
        self.req = req
        self.cfg = cfg

        #If the browser can support it, give it what it wants.
        if 'application/xhtml+xml' in self.req.headers_in.get('Accept', ''):
            self.content_type = 'application/xhtml+xml'
            self.output = 'xhtml'

        self.req.content_type = self.content_type
        
        try:
            self.fields = dict(FieldStorage(self.req))
        except apache.SERVER_RETURN:
            # failed to parse fields; must be an incorrect POST
            # request, so fail with a better error message.
            raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND
        
        self.basePath = normPath(self.cfg.basePath)

        self.siteHandler = SiteHandler()
        self.projectHandler = ProjectHandler()
        self.adminHandler = AdminHandler()
        self.errorHandler = ErrorHandler()
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
        if sid:
            self._session_start()
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
        self.client = shimclient.ShimMintClient(self.cfg, self.authToken)

        self.auth = self.client.checkAuth()
        if self.auth.authorized:
            self.user = self.client.getUser(self.auth.userId)
            self.projectList = self.client.getProjectsByMember(self.auth.userId)
        
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
            self.toUrl = self.cfg.basePath
            err_name = sys.exc_info()[0].__name__
            self.req.log_error("%s: %s" % (err_name, str(e)))
            output = self._write("error", shortError = err_name, error = str(e))
        except fields.MissingParameterError, e:
            output = self._write("error", shortError = "Missing Parameter", error = str(e))
        except mint_error.PermissionDenied, e:
            output = self._write("error", shortError = "Permission Denied", error = str(e))
            
        self.req.write(output)
        return apache.OK
 
    def _getHandler(self, pathInfo):
        fullHost = self.req.hostname
        protocol='https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol='http'
        self.toUrl = ("%s://%s" % (protocol, fullHost)) + self.req.unparsed_uri
        dots = fullHost.split('.')
        hostname = dots[0]

        # if it looks like we're requesting a project (hostname isn't in reserved hosts
        # and doesn't match cfg.hostName, try to request the project.
        if hostname not in mint_server.reservedHosts and hostname != self.cfg.hostName:
            try:
                project = self.client.getProjectByHostname(hostname)
            except Exception, e:
                self.req.log_error(str(e))
                self._redirect(self.cfg.defaultRedirect)
            else:
                # coerce "external" projects to the externalSiteHost, or
                # internal projects to projectSiteHost.
                if project.external: # "external" projects are endorsed by us, so use siteHost
                    self._redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.externalSiteHost, self.cfg.basePath, hostname))
                else:
                    self._redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.projectSiteHost, self.cfg.basePath, hostname))

        self.siteHost = self.cfg.siteHost
        
        # eg., redirect from http://rpath.com -> <defaultRedirect>
        if self.cfg.hostName and fullHost == self.cfg.siteDomainName:
            self._redirect(self.cfg.defaultRedirect)
        
        # mapping of url regexps to handlers
        urls = (
            (r'^/project/',     self.projectHandler),
            (r'^/administer',   self.adminHandler),
            (r'^/repos/',       self.conaryHandler),
            (r'^/unknownError', self.errorHandler),
            (r'^/',             self.siteHandler),
        )

        self.SITE = self.siteHost + self.basePath
        self.isOwner = self.userLevel == userlevels.OWNER or self.auth.admin

        if self.session.has_key('groupTroveId') and self.auth.authorized:
            self.groupTrove = self.client.getGroupTrove(self.session['groupTroveId'])
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

        # match the requested url to the right url handler
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                urlHandler.content_type=self.content_type
                urlHandler.output = self.output
                context['cmd'] = pathInfo[len(match)-1:]
                
                ret = urlHandler.handle(context)
                return ret

        # fell through, nothing matched
        raise apache.SERVER_RETURN, apache.HTTP_NOT_FOUND

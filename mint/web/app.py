#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import base64
import os
import sys
import re
from urllib import quote, unquote

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

from web import fields

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

from webhandler import WebHandler, normPath

class Redirect(Exception):
    def __init__(self, location):
        self.location = location

    def __str__(self):
        return "Location: %s" % self.location

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

    def __init__(self, req, cfg, repServer = None):
        self.req = req
        self.cfg = cfg

        #If the browser can support it, give it what it wants.
        if 'application/xhtml+xml' in self.req.headers_in.get('Accept', ''):
            self.content_type = 'application/xhtml+xml'
            self.output = 'xhtml'

        self.req.content_type = self.content_type
        self.fields = dict(FieldStorage(self.req))
        
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
        self.client = shimclient.ShimMintClient(self.cfg, anonToken)

        # if we are passed a pysid, set the cookie and redirect to the toUrl
        if COOKIE_NAME in self.fields and 'toUrl' in self.fields:
            if self.cfg.cookieSecretKey:
                c = Cookie.SignedCookie(COOKIE_NAME, self.fields.get(COOKIE_NAME),
                                        secret = self.cfg.cookieSecretKey,
                                        domain = self.req.hostname)
            else:
                c = Cookie.Cookie(COOKIE_NAME,
                        self.fields.get(COOKIE_NAME),
                        domain = self.req.hostname)

            self.req.err_headers_out.add('Set-Cookie', str(c))
            self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')
            return self._redirect(unquote(self.fields.get('toUrl')))

        
        # prepare a new session
        sessionClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))
        self.session = SqlSession(self.req, sessionClient,
            secret = self.cfg.cookieSecretKey,
            timeout = 86400, # XXX timeout of one day; should it be configurable?
            domain = self.cfg.siteDomainName,
            lock = False)

        # default to anonToken if the current session has no authToken
        self.authToken = self.session.get('authToken', anonToken)
 
        # open up a new client with the retrieved authToken
        self.client = shimclient.ShimMintClient(self.cfg, self.authToken)
        self.auth = self.client.checkAuth()
 
        # redirect to master site to clone cookie
        if self.session._new and self.req.hostname != self.cfg.siteHost:
            redir = "http://" + self.cfg.siteHost + "/cloneCookie?toUrl=%s;hostname=%s" % (quote(self.req.unparsed_uri), self.req.hostname)
            return self._redirect(redir)

        if self.auth.authorized:
            self.user = self.client.getUser(self.auth.userId)
            self.projectList = self.client.getProjectsByMember(self.auth.userId)
        
        self.auth.setToken(self.authToken)

        try:
            method = self._getHandler(pathInfo)
        except Redirect, e:
            return self._redirect(e.location)
       
        d = self.fields.copy()
        d['auth'] = self.auth
        try:
            returncode = method(**d)
            self.session.save()
            return returncode
        except mint_error.MintError, e:
            self.toUrl = "/"
            err_name = sys.exc_info()[0].__name__
            self.req.log_error("%s: %s" % (err_name, str(e)))
            self._write("error", shortError = err_name, error = str(e))
            return apache.OK
        except fields.MissingParameterError, e:
            self._write("error", shortError = "Missing Parameter", error = str(e))
            return apache.OK
        except mint_error.PermissionDenied, e:
            self._write("error", shortError = "Permission Denied", error = str(e))
            return apache.OK
 
    def _getHandler(self, pathInfo):
        fullHost = self.req.hostname
        protocol='https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol='http'
        self.toUrl = ("%s://%s" % (protocol, fullHost)) + self.req.unparsed_uri
        dots = fullHost.split('.')
        hostname = dots[0]

       
        if hostname not in mint_server.reservedHosts and hostname != self.cfg.hostName:
            try:
                project = self.client.getProjectByHostname(hostname)
            except:
                raise Redirect(self.cfg.defaultRedirect)
            else:
                if project.external: # "external" projects are endorsed by us, so use siteHost
                    raise Redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.siteHost, self.cfg.basePath, hostname))
                else:
                    raise Redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.projectSiteHost, self.cfg.basePath, hostname))

        self.siteHost = self.cfg.siteHost
        self.SITE = self.cfg.siteHost + self.cfg.basePath
        
        if self.cfg.hostName and fullHost == self.cfg.siteDomainName:
            raise Redirect(self.cfg.defaultRedirect)
        
        # mapping of url regexps to handlers
        urls = (
            (r'^/project/',     self.projectHandler),
            (r'^/administer',   self.adminHandler),
            (r'^/repos/',       self.conaryHandler),
            (r'^/unknownError', self.errorHandler),
            (r'^/',             self.siteHandler),
        )

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
            'SITE':             self.SITE,
            'toUrl':            self.toUrl,
            'basePath':         self.basePath,
            'project':          None,
            'userLevel':        self.userLevel,
            'user':             self.user,
        }

        # match the requested url to the right url handler
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                urlHandler.content_type=self.content_type
                urlHandler.output = self.output
                context['cmd'] = pathInfo[len(match)-1:]
                return urlHandler.handle(context)

        # fell through, nothing matched
        return self._404

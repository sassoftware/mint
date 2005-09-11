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

from mint.session import SqlSession
from mint import database
from mint import mint_error
from mint import mint_server
from mint import shimclient
from mint import users

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

class MintApp(WebHandler):
    content_type = "application/xhtml+xml"
    project = None
    projectList = []
    userLevel = -1
    user = None

    def __init__(self, req, cfg, repServer = None):
        self.req = req
        self.cfg = cfg

        self.req.content_type = self.content_type
        
        self.basePath = self.cfg.basePath
        if self.basePath[-1] == '/':
            self.basePath = self.basePath[:-1]

        self.siteHandler = SiteHandler()
        self.projectHandler = ProjectHandler()
        self.adminHandler = AdminHandler()
        if repServer:
            self.conaryHandler = ConaryHandler(req, cfg, repServer)
        else:
            self.conaryHandler = None

    def _handle(self, pathInfo):
        method = self.req.method.upper()
        if method not in ('GET', 'POST'):
            return apache.HTTP_METHOD_NOT_ALLOWED

        anonToken = ('anonymous', 'anonymous')
        self.client = shimclient.ShimMintClient(self.cfg, anonToken)

        # prepare a new session
        sessionClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))
        self.session = SqlSession(self.req, sessionClient,
            secret = self.cfg.cookieSecretKey,
            timeout = 86400, # XXX timeout of one day; should it be configurable?
            domain = self.cfg.domainName)
        
        # default to anonToken if the current session has no authToken
        self.authToken = self.session.get('authToken', anonToken)
       
        # open up a new client with the retrieved authToken
        self.client = shimclient.ShimMintClient(self.cfg, self.authToken)
        self.auth = self.client.checkAuth()
        
        if self.auth.authorized:
            self.user = self.client.getUser(self.auth.userId)
            self.projectList = self.client.getProjectsByMember(self.auth.userId)
        
        self.auth.setToken(self.authToken)

        try:
            method = self._getHandler(pathInfo)
        except Redirect, e:
            return self._redirect(e.location)
           
        d = dict(FieldStorage(self.req))
        d['auth'] = self.auth
        try:
            return method(**d)
        except mint_error.MintError, e:
            err_name = sys.exc_info()[0].__name__
            self.req.log_error("%s: %s" % (err_name, str(e)))
            self._write("error", shortError = err_name, error = str(e))
            return apache.OK
        except fields.MissingParameterError, e:
            self._write("error", shortError = "Missing Parameter", error = str(e))
            return apache.OK

    def _getHandler(self, pathInfo):
        fullHost = self.req.hostname
        self.toUrl = ("http://%s" % fullHost) + self.req.unparsed_uri
        dots = fullHost.split('.')
        hostname = dots[0]

        # slightly hairy logic:
        # if the hostname is the site hostname (eg: mint.rpath.org),
        # great. if it's in reserved hosts, redirect to site hostname.
        # if neither, check to see if it's a valid project. if so,
        # show the project page. if not, redirect to site hostname.
        if self.cfg.hostName:
            siteHost = "%s.%s" % (self.cfg.hostName, self.cfg.domainName)
        else:
            siteHost = self.cfg.domainName
        self.siteHost = siteHost
        
        if self.cfg.hostName and fullHost == self.cfg.domainName:
            raise Redirect(self.cfg.defaultRedirect)
        
        # mapping of url regexps to handlers
        urls = (
            (r'^/project/',     self.projectHandler),
            (r'^/administer',   self.adminHandler),
            (r'^/conary/',      self.conaryHandler),
            (r'^/',             self.siteHandler),
        )

        # a set of information to be passed into the next handler
        context = {
            'auth':             self.auth,
            'authToken':        self.auth.getToken(),
            'client':           self.client,
            'cfg':              self.cfg,
            'projectList':      self.projectList,
            'req':              self.req,
            'session':          self.session,
            'siteHost':         self.siteHost,
            'toUrl':            self.toUrl,
            'basePath':         self.basePath,
            'project':          None,
            'userLevel':        self.userLevel,
            'user':             self.user,
        }

        # match the requested url to the right url handler
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                context['cmd'] = pathInfo[len(match)-1:]
                return urlHandler.handle(context)

        # fell through, nothing matched
        return self._404

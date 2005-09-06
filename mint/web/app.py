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

    def __init__(self, req, cfg):
        self.req = req
        self.cfg = cfg

        self.req.content_type = self.content_type
        
        self.basePath = self.cfg.basePath
        if self.basePath[-1] == '/':
            self.basePath = self.basePath[:-1]

        self.siteHandler = SiteHandler()
        self.projectHandler = ProjectHandler()
        self.adminHandler = AdminHandler()

    def _handle(self, pathInfo):
        method = self.req.method.upper()
        if method not in ('GET', 'POST'):
            return apache.HTTP_METHOD_NOT_ALLOWED

        cookies = Cookie.get_cookies(self.req, Cookie.Cookie)
        if 'authToken' in cookies:
            auth = base64.decodestring(cookies['authToken'].value)
            authToken = auth.split(":")

            auth = self._checkAuth(authToken)

            if not auth.authorized:
                self._clearAuth()
                return self._redirect("/")
            else:
                self.user = self.client.getUser(auth.userId)
                self.projectList = self.client.getProjectsByMember(auth.userId)
        else:
            authToken = ('anonymous', 'anonymous')
            self._checkAuth(authToken)
            auth = users.Authorization()

        self.authToken = authToken
        self.auth = auth
        auth.setToken(authToken)

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

    def _checkAuth(self, authToken):
        self.client = shimclient.ShimMintClient(self.cfg, authToken)
        auth = self.client.checkAuth()
        return auth

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
        
        if len(dots) == 3:
            if hostname == self.cfg.hostName:
                pass
            elif hostname in mint_server.reservedHosts and\
                ".".join(dots[1:]) == self.cfg.domainName:
                raise Redirect(("http://%s" % siteHost) + self.req.unparsed_uri)
            else:
                # redirect to the project page if
                # a project hostname is accessed
                try:
                    project = self.client.getProjectByFQDN(fullHost)
                except database.ItemNotFound:
                    # XXX just for the testing period
                    raise Redirect(self.cfg.defaultRedirect)
                else:
                    raise Redirect("http://%s/project/%s" % (self.siteHost, project.getHostname()))
        elif fullHost == self.cfg.domainName:
            # if hostName is set, require it for access:
            if self.cfg.hostName:
                raise Redirect(self.cfg.defaultRedirect)
                
        # mapping of url regexps to handlers
        urls = (
            (r'^/project/',     self.projectHandler.handle),
#            (r'^/admin/',       self.adminHandler.handle),
            (r'^/',             self.siteHandler.handle),
        )

        # a set of information to be passed into the next handler
        context = {
            'auth':             self.auth,
            'client':           self.client,
            'cfg':              self.cfg,
            'projectList':      self.projectList,
            'req':              self.req,
            'siteHost':         self.siteHost,
            'toUrl':            self.toUrl,
            'basePath':         self.basePath,
            'project':          None,
            'userLevel':        self.userLevel,
        }

        # match the requested url to the right url handler
        for match, urlHandler in urls:
            if re.match(match, pathInfo):
                context['cmd'] = pathInfo[len(match)-1:]
                return urlHandler(context)

        # fell through, nothing matched
        return self._404

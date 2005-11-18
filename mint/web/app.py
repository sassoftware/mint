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

from webhandler import WebHandler, normPath

# hack to set the default encoding to utf-8
# to overcome a kid bug.
reload(sys)
sys.setdefaultencoding("utf-8")

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

    def _session_start(self):
        #from conary.lib import epdb
        #epdb.st()
        # prepare a new session
        sessionClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))

        protocol='https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol='http'
        sid = self.fields.get('sid', None)
        domain = '.'+".".join(self.req.hostname.split(".")[1:])
        self.session = SqlSession(self.req, sessionClient,
            sid = sid,
            secret = self.cfg.cookieSecretKey,
            timeout = 86400, # XXX timeout of one day; should it be configurable?
            domain = domain,
            lock = False)
        if self.session.is_new():
            self.session['firstPage'] = "%s://%s%s" %(protocol, self.req.hostname, self.req.unparsed_uri)
            self.session['visited'] = { }
            self.session['pages'] = [ ]
        #Mark the current domain as visited
        self.session['visited'][domain] = True
        #This is just for debugging purposes
        self.session['pages'].append(self.req.hostname + self.req.unparsed_uri)

        #Now figure out if we need to redirect
        nexthop = None
        for dom in ('.'+self.cfg.siteDomainName, '.'+self.cfg.projectDomainName):
            if not self.session['visited'].get(dom, None):
                #Yeah we need to redirect
                nexthop = dom
                break
        # if we were passed a sid, specifically set a cookie
        # for the requested domain with that sid.
        if sid or nexthop:
            c = self.session.make_cookie()
            c.domain = domain
            #add it to the err_headers_out because these ALWAYS go to the browser
            self.req.err_headers_out.add('Set-Cookie', str(c))
            self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')

        if nexthop:
            #Save the session
            self.session.save()
            raise Redirect("%s://%s.%s%sblank?sid=%s" % (protocol, self.cfg.hostName, nexthop, self.cfg.basePath, self.session.id()))
        else:
            if sid:
                #Clear the sid from the request by redirecting to the first page.
                self.session.save()
                raise Redirect(self.session['firstPage'])

    def _handle(self, pathInfo):
        method = self.req.method.upper()
        if method not in ('GET', 'POST'):
            return apache.HTTP_METHOD_NOT_ALLOWED

        anonToken = ('anonymous', 'anonymous')

        try:
            self._session_start()
        except Redirect, e:
            return self._redirect(e.location)

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
       
        d = self.fields.copy()
        d['auth'] = self.auth

        try:
            returncode = method(**d)
            self.session.save()
            return returncode
        except mint_error.MintError, e:
            self.toUrl = self.cfg.basePath
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

        # if it looks like we're requesting a project (hostname isn't in reserved hosts
        # and doesn't match cfg.hostName, try to request the project.
        if hostname not in mint_server.reservedHosts and hostname != self.cfg.hostName:
            try:
                project = self.client.getProjectByHostname(hostname)
            except Exception, e:
                self.req.log_error(str(e))
                raise Redirect(self.cfg.defaultRedirect)
            else:
                # coerce "external" projects to the externalSiteHost, or
                # internal projects to projectSiteHost.
                if project.external: # "external" projects are endorsed by us, so use siteHost
                    raise Redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.externalSiteHost, self.cfg.basePath, hostname))
                else:
                    raise Redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.projectSiteHost, self.cfg.basePath, hostname))

        self.siteHost = self.cfg.siteHost
        
        # eg., redirect from http://rpath.com -> <defaultRedirect>
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
        return self._404

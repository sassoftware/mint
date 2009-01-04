#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import kid
import re
import sys
import time

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

from mint.client import timeDelta
from mint import server
from mint import shimclient
from mint import userlevels
from mint.helperfuncs import (formatHTTPDate, getProjectText,
    weak_signature_call)
from mint.mint_error import *
from mint.web import fields
from mint.web.admin import AdminHandler
from mint.web.project import ProjectHandler
from mint.web.appliance_creator import APCHandler
from mint.web.repos import ConaryHandler
from mint.web.site import SiteHandler
from mint.web.webhandler import (WebHandler, normPath, setCacheControl,
    HttpNotFound)
from mint import maintenance

stagnantAllowedPages = ['editUserSettings','confirm','logout', 'continueLogout', 'validateSession']

# called from hooks.py if an exception was not caught
class ErrorHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
        return self.errorPage

    def errorPage(self, *args, **kwargs):
        return self._write('error', error = ' An unknown error occurred while handling your request. Site maintainers have been notified.')


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
        self.apcHandler = APCHandler()
        self.projectHandler = ProjectHandler()
        self.adminHandler = AdminHandler()
        self.errorHandler = ErrorHandler()
        self.conaryHandler = ConaryHandler(req, cfg, repServer)

    def _handle(self, pathInfo):
        method = self.req.method.upper()
        if method not in ('GET', 'POST', 'PUT'):
            return apache.HTTP_METHOD_NOT_ALLOWED

        anonToken = ('anonymous', 'anonymous')

        try:
            if self.cfg.cookieSecretKey:
                cookies = Cookie.get_cookies(self.req, Cookie.SignedCookie, secret = self.cfg.cookieSecretKey)
            else:
                cookies = Cookie.get_cookies(self.req, Cookie.Cookie)
        except:
            # Parsing the cookies failed, so just pretend there aren't
            # any and they'll get overwritten when our response goes
            # out.
            cookies = {}

        if 'pysid' in cookies:
            self._session_start()

        # default to anonToken if the current session has no authToken
        self.authToken = self.session.get('authToken', anonToken)

        # open up a new client with the retrieved authToken
        self.client = shimclient.ShimMintClient(self.cfg, self.authToken)

        self.auth = self.client.checkAuth()
        self.membershipReqsList = None
        if self.auth.authorized:
            if not maintenance.getMaintenanceMode(self.cfg) or self.auth.admin:
                self.user = self.client.getUser(self.auth.userId)
                self.projectList = self.client.getProjectsByMember(self.auth.userId)
                self.projectDict = {}
                for project, level, memberReqs in self.projectList:
                    l = self.projectDict.setdefault(level, [])
                    l.append((project, memberReqs))
                self.membershipReqsList = [x[0] for x in self.projectList
                        if x[2] > 0 and x[1] == userlevels.OWNER]
            else:
                if pathInfo not in  ('/maintenance/', '/logout/'):
                    raise MaintenanceMode
        self.auth.setToken(self.authToken)

        method = self._getHandler(pathInfo)

        d = self.fields.copy()
        d['auth'] = self.auth

        def logTraceback():
            import traceback
            e_type, e_value, e_tb = sys.exc_info()

            short = ''.join(traceback.format_exception_only(
                e_type, e_value))
            self.req.log_error("Handled user error: (not a bug)")
            sys.stderr.write(short)
            sys.stderr.flush()

            formatted = ''.join(traceback.format_exception(
                e_type, e_value, e_tb))
            return formatted

        try:
            output = weak_signature_call(method, **d)
        except MintError, e:
            if isinstance(e, MaintenanceMode):
                raise
            tb = logTraceback()
            self.toUrl = self.cfg.basePath
            err_name = sys.exc_info()[0].__name__
            setCacheControl(self.req, strict=True)
            output = self._write("error", shortError = err_name, error = str(e),
                traceback = self.cfg.debugMode and tb or None)
        except fields.MissingParameterError, e:
            tb = logTraceback()
            setCacheControl(self.req, strict=True)
            output = self._write("error", shortError = "Missing Parameter", error = str(e))
        except fields.BadParameterError, e:
            tb = logTraceback()
            setCacheControl(self.req, strict=True)
            output = self._write("error", shortError = "Bad Parameter", error = str(e),
                traceback = self.cfg.debugMode and tb or None)
        else:
            if self.auth.authorized:
                self.session.save()
            setCacheControl(self.req)
            self.req.headers_out['Last-modified'] = formatHTTPDate()

        self.req.set_content_length(len(output))
        self.req.write(output)
        self._clearAllMessages()
        return apache.OK

    def _getHandler(self, pathInfo):
        fullHost = self.req.headers_in.get('host', self.req.hostname)
        protocol='https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol='http'

        # get remote IP address (try HTTP_X_FORWARDED_FOR first, in case
        # we are behind a proxy
        self.remoteIp = self.req.headers_in.get("X-Forwarded-For",
                self.req.connection.remote_ip)

        # sanitize IP just in case it's a list of proxied hosts
        self.remoteIp = self.remoteIp.split(',')[0]

        args = self.req.args and "?" + self.req.args or ""
        self.toUrl = ("%s://%s" % (protocol, fullHost)) + self.req.uri + args
        dots = fullHost.split(':')[0].split('.')
        hostname = dots[0]

        # if it looks like we're requesting a project (hostname isn't in reserved hosts
        # and doesn't match cfg.hostName, try to request the project.
        if hostname not in server.reservedHosts \
            and hostname != self.cfg.hostName \
            and self.cfg.configured:
            self._redirect("%s://%s%sproject/%s/" % (protocol, self.cfg.projectSiteHost, self.cfg.basePath, hostname))

        self.siteHost = self.cfg.siteHost

        # redirect from domain.org to host.domain.org
        if self.cfg.hostName and fullHost == self.cfg.siteDomainName:
            self._redirect('http://' + self.cfg.hostName + "." + self.cfg.siteDomainName)

        # mapping of url regexps to handlers
        urls = (
            (r'^/apc/',         self.apcHandler),
            (r'^/project/',     self.projectHandler),
            (r'^/admin/',  self.adminHandler),
            (r'^/administer/',  self.adminHandler),
            (r'^/repos/',       self.conaryHandler),
            (r'^/unknownError', self.errorHandler),
            (r'^/',             self.siteHandler),
        )

        self.SITE = self.siteHost + self.basePath
        self.isOwner = self.userLevel == userlevels.OWNER or self.auth.admin

        if self.session.has_key('groupTroveId') and self.auth.authorized:
            try:
                self.groupTrove = self.client.getGroupTrove(self.session['groupTroveId'])
            except ItemNotFound:
                del self.session['groupTroveId']
                self.groupTrove = None
                self.groupProject = None
            else:
                self.groupProject = self.client.getProject(self.groupTrove.projectId)
        else:
            self.groupTrove = None
            self.groupProject = None

        # Handle messages stashed in the session
        self.infoMsg = self.session.setdefault('infoMsg', '')
        self.searchType = self.session.setdefault('searchType', getProjectText().title()+"s")
        self.searchTerms = ''
        self.errorMsgList = self._getErrors()

        # get the news for the frontpage (only in non-maint mode)
        self.latestRssNews = dict()
        if not maintenance.getMaintenanceMode(self.cfg):
            newNews = self.client.getNews()
            if len(newNews) > 0:
                self.latestRssNews = newNews[0]
                if 'pubDate' in self.latestRssNews:
                    self.latestRssNews['age'] = \
                            timeDelta(self.latestRssNews['pubDate'],
                                    capitalized=False)

        # a set of information to be passed into the next handler
        context = {
            'auth':             self.auth,
            'authToken':        self.auth.getToken(),
            'client':           self.client,
            'cfg':              self.cfg,
            'fields':           self.fields,
            'projectList':      self.projectList,
            'projectDict':      self.projectDict,
            'membershipReqsList': self.membershipReqsList,
            'req':              self.req,
            'session':          self.session,
            'siteHost':         self.cfg.siteHost,
            'searchType':       self.searchType,
            'searchTerms':      '',
            'toUrl':            self.toUrl,
            'basePath':         self.basePath,
            'project':          None,
            'SITE':             self.SITE,
            'userLevel':        self.userLevel,
            'user':             self.user,
            'isOwner':          self.isOwner,
            'groupTrove':       self.groupTrove,
            'groupProject':     self.groupProject,
            'infoMsg':          self.infoMsg,
            'errorMsgList':     self.errorMsgList,
            'output':           self.output,
            'remoteIp':         self.remoteIp,
            'latestRssNews':    self.latestRssNews
        }

        if self.auth.stagnant and ''.join(pathInfo.split('/')) not in stagnantAllowedPages:
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

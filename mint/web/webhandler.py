#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import os
import textwrap
import time
import sys

import kid

from mod_python import apache
from mod_python import Cookie

from mint import users
from cache import pageCache, reqHash

from mint import shimclient
from mint.session import SqlSession
from mint import profile

kidCache = {}

class WebHandler(object):
    """Mixin class for various helpful web methods."""

    #Default content-type to send to browser
    content_type='text/html'
    #Default render type to send to kid
    output = 'html-strict'

    def _write(self, templateName, templatePath = None, **values):
        prof = profile.Profile(self.cfg)
        wasCacheHit = False

        if not templatePath:
            templatePath = self.cfg.templatePath

        path = os.path.join(templatePath, templateName + ".kid")
        prof.startKid(templateName)

        if not self.cfg.debugMode:
            global kidCache
            #TODO Refresh if it's changed
            if templateName not in kidCache:
                kidCache[templateName] = kid.load_template(path)
            else:
                wasCacheHit = True
            template = kidCache[templateName]
        else:
            template = kid.load_template(path)

        t = template.Template(cfg = self.cfg,
                              auth = self.auth,
                              project = self.project,
                              userLevel = self.userLevel,
                              projectList = self.projectList,
                              projectDict = self.projectDict,
                              req = self.req,
                              session = self.session,
                              siteHost = self.siteHost,
                              toUrl = self.toUrl,
                              basePath = self.basePath,
                              SITE = self.SITE,
                              isOwner = self.isOwner,
                              groupTrove = self.groupTrove,
                              groupProject = self.groupProject,
                              output = self.output,
                              **values)

        t.assume_encoding = 'utf-8' # tell kid to assume that all input is utf-8
        returner = t.serialize(encoding = "utf-8", output = self.output)
        prof.stopKid(templateName, wasCacheHit)

        return returner

    def _redirectHttp(self, location):
        if location.startswith('http://'):
            pass
        elif location.startswith('https://'):
            location = location.replace('https://', 'http://', 1)
        else:
            while location and location[0] == '/':
                location = location[1:]
            location = 'http://%s%s%s' % \
                       (self.req.headers_in.get('host', self.req.hostname),
                        self.cfg.basePath, location)

        sys.stderr.flush()
        self._redirect(location)

    def _redirect(self, location, temporary = False):
        self.req.headers_out['Location'] = location

        if temporary:
            raise HttpMovedTemporarily
        else:
            raise HttpMoved

    def _clearAuth(self):
        self.auth = users.Authorization()
        self.authToken = ('anonymous', 'anonymous')
        #Add additional data to clear here
        if 'firstTimer' in self.session.keys():
            del self.session['firstTimer']

        self.session['authToken'] = self.authToken
        self.session.invalidate()

    def _resetPasswordById(self, userId):
        newpw = users.newPassword()
        user = self.client.getUser(userId)
        user.setPassword(newpw)

        message = "\n".join(["Your password for username %s at %s has been reset to:" % (user.getUsername(), self.cfg.productName),
                             "",
                             "    %s" % newpw,
                             "",
                             "Please log in at http://%s.%s/ and change" %
                             (self.cfg.hostName, self.cfg.siteDomainName),
                             "this password as soon as possible."
                             ])

        users.sendMail(self.cfg.adminMail, self.cfg.productName,
                   user.getEmail(),
                   "%s forgotten password"%self.cfg.productName, message)

    def _writeRss(self, **values):
        if "rss20.kid" not in kidCache:
            path = os.path.join(self.cfg.templatePath, "rss20.kid")
            kidCache["rss20.kid"] = kid.load_template(path)

        template = kidCache["rss20.kid"]
        t = template.Template(**values)
        self.req.content_type = "text/xml"
        return t.serialize(encoding = "utf-8", output = "xml")

    def _protocol(self):
        protocol = 'https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol = 'http'
        return protocol

    def _session_start(self):
        sid = self.fields.get('sid', None)
        # prepare a new session

        sessionClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))

        if self.cfg.configured:
            domain = ".".join(self.req.hostname.split(".")[1:])
            cookieDomain = "." + domain
        else:
            domain = cookieDomain = self.req.hostname

        self.session = SqlSession(self.req, sessionClient,
            sid = sid,
            secret = self.cfg.cookieSecretKey,
            timeout = 86400, # XXX timeout of one day; should it be configurable?
            domain = cookieDomain,
            lock = False)
        if self.session.is_new():
            self.session['firstPage'] = "%s://%s%s" % ( \
                self._protocol(), \
                self.req.headers_in.get('host', self.req.hostname), '/')
            self.session['visited'] = { }
        #Mark the current domain as visited
        self.session['visited'][domain] = True

        c = self.session.make_cookie()

        if self.session.get('rememberMe', False):
            c.expires = 1209600 + time.time()
            # ensure timeout is 2 weeks for remembered sessions
            if self.session.timeout() != 1209600:
                self.session.set_timeout(1209600)
                self.session.save()

        c.domain = cookieDomain
        #add it to the err_headers_out because these ALWAYS go to the browser
        self.req.err_headers_out.add('Set-Cookie', str(c))
        self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')

    def _redirect_storm(self, sid):
        #Now figure out if we need to redirect
        nexthop = None
        # split is used to ensure port number doesn't affect cookie domain
        for dom in (self.cfg.siteDomainName.split(':')[0],
                    self.cfg.projectDomainName.split(':')[0]):
            if not self.session['visited'].get(dom, None):
                #Yeah we need to redirect
                nexthop = dom
                break
        # if we were passed a sid, specifically set a cookie
        # for the requested domain with that sid.
        if sid or nexthop:
            c = self.session.make_cookie()

            if self.session.get('rememberMe', False):
                c.expires = 1209600 + time.time()
                # ensure timeout is 2 weeks for remembered sessions
                if self.session.timeout() != 1209600:
                    self.session.set_timeout(1209600)
                    self.session.save()

            c.domain = '.' + ".".join(self.req.hostname.split(".")[1:])
            #add it to the err_headers_out because these ALWAYS go to the browser
            self.req.err_headers_out.add('Set-Cookie', str(c))
            self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')
        if nexthop:
            #Save the session
            self.session.save()
            self._redirect("http://%s.%s%sblank?sid=%s" % (self.cfg.hostName, nexthop, self.cfg.basePath, self.session.id()))
        else:
            if sid:
                #Clear the sid from the request by redirecting to the first page.
                self.session.save()
                self._redirect(self.session['firstPage'])


def normPath(path):
    """Normalize a web path by prepending a / if missing, and appending
    a / if missing."""
    if path == "":
        path = "/"
    elif path[-1] != "/":
        path += "/"
    if path[0] != "/":
        path = "/" + path
    path = path.replace('//', '/')
    return path


class HttpError(Exception):
    def __str__(self):
        return "HTTP error %d" % self.code

class HttpNotFound(HttpError):
    code = 404

class HttpForbidden(HttpError):
    code = 403

class HttpMoved(HttpError):
    code = 301

class HttpMovedTemporarily(HttpError):
    code = 302

class HttpOK(HttpError):
    code = 200

class HttpPartialContent(HttpError):
    code = 206

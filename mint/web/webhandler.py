#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import base64
import kid
from kid.pull import START, TEXT, END

import os
import time

import gettext

from mod_python import apache

from mint import helperfuncs
from mint import shimclient
from mint import profile
from mint import users
from mint.session import SqlSession

class HttpError(Exception):
    def __str__(self):
        return "HTTP error %d" % self.code
class HttpOK(HttpError):                code = 200
class HttpPartialContent(HttpError):    code = 206
class HttpMoved(HttpError):             code = 301
class HttpMovedTemporarily(HttpError):  code = 302
class HttpForbidden(HttpError):         code = 403
class HttpNotFound(HttpError):          code = 404
class HttpMethodNotAllowed(HttpError):  code = 405

class WebHandler(object):
    """Mixin class for various helpful web methods."""

    #Default content-type to send to browser
    content_type='text/html; charset=utf-8'

    #Default render type to send to kid
    output = 'xhtml-strict'

    def _write(self, templateName, templatePath = None, **values):
        prof = profile.Profile(self.cfg)
        wasCacheHit = False

        if not templatePath:
            templatePath = self.cfg.templatePath

        path = os.path.join(templatePath, templateName + ".kid")
        prof.startKid(templateName)

        template = kid.load_template(path)

        # pass along the context (overridden by values passed in as
        # kwargs to _write)
        context = dict(self.__dict__.iteritems())
        context.update(values)
        context.update({'cacheFakeoutVersion': helperfuncs.getVersionForCacheFakeout()})

        # Check for a bulletin file
        if os.path.exists(self.cfg.bulletinPath):
            bulletin = open(self.cfg.bulletinPath).read()
        else:
            bulletin = ''
        context.update({'bulletin': bulletin})

        # write out the template
        t = template.Template(**context)

        lang = self.cfg.language
        if lang != 'en':
            xlator = make_i18n_filter(self.cfg.localeDir, lang)
            t._filters.append(xlator)

        t.assume_encoding = 'latin1'
        returner = t.serialize(encoding = "utf-8", output = self.output)
        prof.stopKid(templateName, wasCacheHit)

        return returner

    def _redirectHttp(self, location):
        if ':' in self.cfg.externalDomainName:
            httpPort = int(self.cfg.externalDomainName.split(':')[1])
        else:
            httpPort = 80

        while location and location[0] == '/':
            location = location[1:]

        hostname = self.req.headers_in.get('host', self.req.hostname)
        if ':' not in hostname and httpPort != 80:
            hostname = '%s:%i' % \
                   (hostname, httpPort)

        location = 'http://%s%s%s' % \
                   (hostname, self.cfg.basePath, location)

        self._redirect(location)

    def _redirect(self, location, temporary = False):
        self.req.err_headers_out['Cache-Control'] = "no-store"
        if not location.startswith('http'):
            self.req.log_error("ERROR IN REDIRECT: " + location)
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
        if self.session and isinstance(self.session, SqlSession):
            self.session.invalidate()

    def _resetPasswordById(self, userId):
        newpw = users.newPassword()
        adminClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))
        user = adminClient.getUser(userId)
        user.setPassword(newpw)

        message = "\n".join(["Your password for username %s at %s has been reset to:" % (user.getUsername(), self.cfg.productName),
                             "",
                             "    %s" % newpw,
                             "",
                             "Please log in at http://%s.%s/ and change" %
                             (self.cfg.hostName, self.cfg.siteDomainName),
                             "this password as soon as possible."
                             ])

        if self.cfg.sendNotificationEmails:
            users.sendMail(self.cfg.adminMail, self.cfg.productName,
                       user.getEmail(),
                       "%s password reset"%self.cfg.productName, message)
        else:
            self.req.log_error("The password for %s has been reset to %s" % (user.username, newpw))

    def _writeRss(self, **values):
        path = os.path.join(self.cfg.templatePath, "rss20.kid")
        template = kid.load_template(path)

        t = template.Template(**values)
        t.assume_encoding = 'latin1'
        self.req.content_type = "text/xml"
        return t.serialize(encoding = "utf-8", output = "xml")

    def _protocol(self):
        protocol = 'https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol = 'http'
        return protocol

    def _session_start(self, rememberMe = False):
        sid = self.fields.get('sid', None)

        sessionClient = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser, self.cfg.authPass))

        self.session = SqlSession(self.req, sessionClient,
            sid = sid,
            secret = self.cfg.cookieSecretKey,
            timeout = 86400,
            lock = False)

        if self.session.is_new():
            self.session['firstPage'] = "%s://%s%s" % ( \
                self._protocol(), \
                self.req.headers_in.get('host', self.req.hostname), '/')
            self.session['visited'] = { }
            self.session['rememberMe'] = rememberMe
        else:
            rememberMe = self.session['rememberMe']

        c = self.session.make_cookie()

        if rememberMe:
            c.expires = 1209600 + time.time()
            # ensure timeout is 2 weeks for remembered sessions
            if self.session.timeout() != 1209600:
                self.session.set_timeout(1209600)

        self.req.err_headers_out.add('Set-Cookie', str(c))
        self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')

        # mark the current domain as visited
        self.session['visited'][self.req.hostname] = True

    def _getNextHop(self):
        #Now figure out if we need to redirect
        nexthop = None
        # split is used to ensure port number doesn't affect cookie domain
        for dom in (self.cfg.siteDomainName.split(':'),
                    self.cfg.projectDomainName.split(':')):
            visitedHost = "%s.%s" % (self.cfg.hostName, dom[0])
            if not self.session['visited'].get(visitedHost, False):
                #Yeah we need to redirect
                nexthop = "%s.%s" % (self.cfg.hostName, ':'.join(dom))
                break
        return nexthop

    # Methods used to stash away info/error messages into the session.
    # These variables are retrieved and deleted automatically by
    # mint/web/app.py when building the context for handling a request.
    #
    # NOTE: This requires a *real* persistent session to work properly.
    # Currently, rBO only doles out a real session if a user is logged in.

    def _setInlineMime(self, src, **kwargs):
        inlineMime = (src, [x for x in kwargs.iteritems()])
        self.session['inlineMime'] = inlineMime
        if (isinstance(self.session, SqlSession)):
            self.session.save()

    def _setInfo(self, message):
        self.session['infoMsg'] = message
        self.infoMsg = message
        if (isinstance(self.session, SqlSession)):
            self.session.save()

    def _getErrors(self):
        return self.session.setdefault('errorMsgList', [])

    def _addErrors(self, message):
        errorMsgList = self._getErrors()
        errorMsgList.append(message)
        self.session['errorMsgList'] = errorMsgList
        if (isinstance(self.session, SqlSession)):
            self.session.save()

    def _clearAllMessages(self):
        if (isinstance(self.session, SqlSession)):
            for key in ('infoMsg', 'errorMsgList', 'inlineMime'):
                if self.session.has_key(key):
                    del self.session[key]
            self.session.save()

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


def getHttpAuth(req):
    # special header to pass a session id through
    # instead of a real http authorization token
    if 'X-Session-Id' in req.headers_in:
        return req.headers_in['X-Session-Id']

    if not 'Authorization' in req.headers_in:
        authToken = ['anonymous', 'anonymous']
    else:
        info = req.headers_in['Authorization'].split()
        if len(info) != 2 or info[0] != "Basic":
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

        try:
            authString = base64.decodestring(info[1])
        except:
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

        if authString.count(":") != 1:
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST

        authToken = authString.split(":")

    entitlement = req.headers_in.get('X-Conary-Entitlement', None)
    if entitlement is not None:
        try:
            entitlement = entitlement.split()
            entitlement[1] = base64.decodestring(entitlement[1])
        except:
            raise apache.SERVER_RETURN, apache.HTTP_BAD_REQUEST
    else:
        entitlement = [ None, None ]

    return authToken + entitlement


catalogs = {}
def get_catalog(locale, localeDir):
    return gettext.translation(domain='rBuilder',
            localedir=localeDir, languages=[locale])


def make_i18n_filter(localeDir, locale = 'en'):
    xl = locale
    if locale not in catalogs:
        catalogs[locale] = get_catalog(locale, localeDir)
    catalog = catalogs[locale]

    def i18n_filter(stream, template):
        """Kid template filter which calls translates all elements matching language
        attribute.
        """
        lang_attr = "lang"
        locales=[xl]

        for ev, item in stream:
            if ev==START:
                l = item.get(lang_attr)
                if l:
                    locale = l
                    locales.append(l)
            elif ev==TEXT:
                prefix = ''
                postfix = ''
                if len(item) > 0 and item[0] == ' ': prefix =' '
                if len(item) > 1 and item[-1] == ' ': postfix =' '
                text = item.strip()
                if text:
                    item = catalog.ugettext(text)
                    item = prefix + item + postfix
            elif ev==END:
                if item.get(lang_attr):
                    locales.pop()
                    locale = locales[-1]
            yield (ev, item)

    return i18n_filter

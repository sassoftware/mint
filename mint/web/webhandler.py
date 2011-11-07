#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All rights reserved
#
import base64
import kid
import kid.parser
from kid.parser import START, TEXT, END


import os
import time

import gettext

from conary.lib import util

from mod_python import apache
from mod_python import Cookie

from mint import helperfuncs
from mint import shimclient
from mint.lib import maillib
from mint.lib import profile
from mint import users
from mint.session import SqlSession

class HttpError(Exception):
    code = -1
    def __str__(self):
        return "HTTP error %d" % self.code
class HttpOK(HttpError):                code = 200
class HttpPartialContent(HttpError):    code = 206
class HttpMoved(HttpError):             code = 301
class HttpMovedTemporarily(HttpError):  code = 302
class HttpBadRequest(HttpError):        code = 400
class HttpForbidden(HttpError):         code = 403
class HttpNotFound(HttpError):          code = 404
class HttpMethodNotAllowed(HttpError):  code = 405

class WebHandler(object):
    """Mixin class for various helpful web methods."""

    #Default content-type to send to browser
    content_type='text/html; charset=utf-8'

    #Default render type to send to kid
    output = 'xhtml-strict'

    cfg = None
    db = None
    req = None

    basePath = None
    baseUrl = None

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

    def _redirectHttp(self, location='', temporary=False):
        self._redirect(location, temporary=temporary)

    def _redirect(self, location, temporary = False):
        if '://' not in location:
            while location and location[0] == '/':
                location = location[1:]
            location = self.baseUrl + location
        setCacheControl(self.req, strict=True)
        self.req.headers_out['Location'] = location

        if temporary:
            raise HttpMovedTemporarily
        else:
            raise HttpMoved

    def _redirectOldLinks(self, location=''):
        """
        Mechanism to redirect old UI links to the new UI when not prefixed by
        /web/
        """
        redirectIndex = self.req.get_options().get('redirectIndex', False)
        if redirectIndex:
            self._redirectHttp('ui/' + location)

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
        adminClient = shimclient.ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db)
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
            maillib.sendMail(self.cfg.adminMail, self.cfg.productName,
                       user.getEmail(),
                       "%s password reset"%self.cfg.productName, message)
        else:
            self.req.log_error("The password for %s has been reset to %s" % (user.username, newpw))

    def _protocol(self):
        protocol = 'https'
        if self.req.subprocess_env.get('HTTPS', 'off') != 'on':
            protocol = 'http'
        return protocol

    def _session_start(self, rememberMe = False):
        sid = self.fields.get('sid', None)

        sessionClient = shimclient.ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db)

        self.session = SqlSession(self.req, sessionClient,
            sid = sid,
            timeout = 86400,
            lock = False)

        if self.session.is_new():
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

    # Methods used to stash away info/error messages into the session.
    # These variables are retrieved and deleted automatically by
    # mint/web/app.py when building the context for handling a request.
    #
    # NOTE: This requires a *real* persistent session to work properly.
    # Currently, rBO only doles out a real session if a user is logged in.

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
        for key in ('infoMsg', 'errorMsgList'):
            if self.session.has_key(key):
                del self.session[key]
        if (isinstance(self.session, SqlSession)):
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

    # pysid cookies are just as good as the session id - flex uses the browser
    # for authentication info and cookies are sent for free. (RBL-4276)
    cookies = Cookie.get_cookies(req, Cookie.Cookie)
    if 'pysid' in cookies:
        return cookies['pysid'].value

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
        authToken[1] = util.ProtectedString(authToken[1])

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
            yield (ev, item)

    return i18n_filter


def setCacheControl(req, strict=False):
    """
    Set the Cache-Control header for dynamically generated content.

    These flags are used:
     * private - Responses are specific to each user agent, so only
       private caches (like the one built into the user agent, as
       opposed to a shared proxy cache) may store. We can probably
       omit this if the user is not logged in as it may save
       some traffic.
     * max-age=0 - Content is stale immediately after it is
       received.
     * must-revalidate - Always ask the server for another copy
       once content is stale, which due to the above directive
       means every time.

    Effectively, these three will allow the cache to store
    responses, but never use them to respond to a request without
    first asking the server to fufill the request and then
    comparing the fresh content from the server to the previous
    cached value. This way, client conditions like
    If-Modified-Since can still work since the cache can check
    them against the now revalidated cached data.

    If C{strict} is C{True}, "no-cache" will be used in place of
    the "max-age" and "must-revalidate" fields. This should be used
    for contentless responses such as redirects, or temporary
    issues like bad logins.
    """
    if strict:
        cacheFlags = 'private, no-cache'
    else:
        cacheFlags = 'private, must-revalidate, max-age=0'
    req.err_headers_out['Cache-control'] = cacheFlags

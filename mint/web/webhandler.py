#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import gettext
import logging
import kid
import os
from conary.web import webauth
from kid.parser import START, TEXT, END
from webob import exc as web_exc

from mint import helperfuncs
from mint import shimclient
from mint.lib import maillib
from mint.lib import profile
from mint import users

log = logging.getLogger(__name__)


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

    def _redirectHttp(self, location='', temporary=True):
        self._redirect(location, temporary=temporary)

    def _redirect(self, location, temporary = False):
        if '://' not in location:
            while location and location[0] == '/':
                location = location[1:]
            location = self.baseUrl + location
        if temporary:
            raise web_exc.HTTPFound(location=location)
        else:
            raise web_exc.HTTPMovedPermanently(location=location)

    def _redirectOldLinks(self, location=''):
        """
        Mechanism to redirect old UI links to the new UI when not prefixed by
        /web/
        """
        self._redirectHttp('api')

    def _clearAuth(self):
        self.auth = users.Authorization()
        self.authToken = ('anonymous', 'anonymous')
        self.session['authToken'] = self.authToken
        self.session.invalidate()

    def _resetPasswordById(self, userId):
        newpw = users.newPassword()
        adminClient = shimclient.ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db)
        user = adminClient.getUser(userId)

        if not user.passwd:
            raise Exception("not permitted to reset the password of an external auth account")

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
            log.info("The password for %s has been reset to %s" % (user.username, newpw))

    # Methods used to stash away info/error messages into the session.
    # These variables are retrieved and deleted automatically by
    # mint/web/app.py when building the context for handling a request.
    #
    # NOTE: This requires a *real* persistent session to work properly.
    # Currently, rBO only doles out a real session if a user is logged in.

    def _setInfo(self, message):
        self.session['infoMsg'] = message
        self.infoMsg = message
        self.session.save()

    def _getErrors(self):
        return self.session.setdefault('errorMsgList', [])

    def _addErrors(self, message):
        errorMsgList = self._getErrors()
        errorMsgList.append(message)
        self.session['errorMsgList'] = errorMsgList
        self.session.save()

    def _clearAllMessages(self):
        for key in ('infoMsg', 'errorMsgList'):
            if self.session.get(key):
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
    if 'X-Session-Id' in req.headers:
        return req.headers['X-Session-Id']

    # pysid cookies are just as good as the session id - flex uses the browser
    # for authentication info and cookies are sent for free. (RBL-4276)
    if 'pysid' in req.cookies:
        return req.cookies['pysid']

    return webauth.getAuth(req)


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

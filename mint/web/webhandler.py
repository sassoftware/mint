#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import kid
import os
import time
import sys

from mod_python import apache
from mod_python import Cookie

from mint import users

kidCache = {}

class WebHandler(object):
    #Default content-type to send to browser
    content_type='text/html'
    #Default render type to send to kid
    output = 'html-strict'

    """Mixin class for various helpful web methods."""
    def _write(self, template, templatePath = None, **values):
        startTime = time.time()
        if not templatePath:
            templatePath = self.cfg.templatePath

        global kidCache
        if template not in kidCache:
            path = os.path.join(templatePath, template + ".kid")
            kidCache[template] = kid.load_template(path)
        
        template = kidCache[template]
        t = template.Template(cfg = self.cfg,
                              auth = self.auth,
                              project = self.project,
                              userLevel = self.userLevel,
                              projectList = self.projectList,
                              req = self.req,
                              session = self.session,
                              siteHost = self.siteHost,
                              toUrl = self.toUrl,
                              basePath = self.basePath,
                              SITE = self.SITE,
                              **values)
        s = t.serialize(encoding = "utf-8", output = self.output)
        print >> sys.stderr, "Kid page rendered: %.2f" % ((time.time() - startTime) * 1000)
        self.req.write(s)

    def _404(self, *args, **kwargs):
        return apache.HTTP_NOT_FOUND

    def _redirectHttp(self, location):
        if location.startswith('http://'):
            pass
        elif location.startswith('https://'):
            location = location.replace('https://', 'http://', 1)
        else:
            while location and location[0] == '/':
                location = location[1:]
            location = 'http://%s%s%s' % (self.req.hostname, self.cfg.basePath, location)
        self.req.headers_out['Location'] = location
        return apache.HTTP_MOVED_PERMANENTLY

    def _redirect(self, location):
        self.req.headers_out['Location'] = location
        return apache.HTTP_MOVED_PERMANENTLY

    def _redirector(self, location):
        def wrapper(*args, **kwargs):
            return self._redirect(location)
        return wrapper

    def _clearAuth(self):
        self.auth = users.Authorization()
        self.authToken = ('anonymous', 'anonymous')
        #Add additional data to clear here
        if 'firstTimer' in self.session.keys():
            del self.session['firstTimer']

        self.session['authToken'] = self.authToken
        # Don't invalidate the session.  This should save a redirect storm

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
        s = t.serialize(encoding = "utf-8", output = "xml")
        self.req.write(s)


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

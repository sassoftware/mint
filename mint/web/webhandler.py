#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import kid
import os
import time

from mod_python import apache
from mod_python import Cookie

from mint import users

class WebHandler(object):
    """Mixin class for various helpful web methods."""
    def _write(self, template, templatePath = None, **values):
        if not templatePath:
            templatePath = self.cfg.templatePath
        path = os.path.join(templatePath, template + ".kid")
        template = kid.load_template(path)
        t = template.Template(cfg = self.cfg,
                              auth = self.auth,
                              project = self.project,
                              userLevel = self.userLevel,
                              projectList = self.projectList,
                              req = self.req,
                              siteHost = self.siteHost,
                              toUrl = self.toUrl,
                              basePath = self.basePath,
                              **values)
        t.write(self.req, encoding = "utf-8", output = "xhtml-strict")

    def _404(self, *args, **kwargs):
        return apache.HTTP_NOT_FOUND

    def _redirect(self, location):
        self.req.headers_out['Location'] = location
        return apache.HTTP_MOVED_PERMANENTLY

    def _redirCookie(self, cookie):
        # we have to add the cookie headers manually when redirecting, because
        # mod_python looks at err_headers_out instead of headers_out.

        self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
        self.req.err_headers_out.add("Set-Cookie", str(cookie))

    def _clearAuth(self):
        self.auth = users.Authorization()
        self.authToken = ('anonymous', 'anonymous')
        for domain in self.cfg.cookieDomain:
            cookie = Cookie.Cookie('authToken', '', domain = "." + domain,
                                                    expires = time.time() - 300,
                                                    path = "/")
            self._redirCookie(cookie)

def normPath(path):
    """Normalize a web path by prepending a / if missing, and appending
    a / if missing."""
    if path == "":
        path = "/"
    elif path[-1] != "/":
        path += "/"
    if path[0] != "/":
        path = "/" + path
    return path

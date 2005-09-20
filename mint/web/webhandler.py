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
    #Default content-type to send to browser
    content_type='text/html'
    #Default render type to send to kid
    output = 'html-strict'

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
        t.write(self.req, encoding = "utf-8", output = self.output)

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

    def _clearAuth(self):
        self.auth = users.Authorization()
        self.authToken = ('anonymous', 'anonymous')
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
                             (self.cfg.hostName, self.cfg.domainName),
                             "this password as soon as possible."
                             ])

        users.sendMail(self.cfg.adminMail, self.cfg.productName,
                   user.getEmail(),
                   "%s forgotten password"%self.cfg.productName, message)


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

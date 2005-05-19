#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import base64
import os
import kid
import sys

from mod_python import apache
from mod_python import Cookie

from conary.web import webhandler
from conary.web.fields import strFields, intFields, listFields, boolFields

from mint import shimclient
from mint import projects
from mint import database

def log(*args):
    print >> sys.stderr, args
    sys.stderr.flush()

class MintApp(webhandler.WebHandler):
    def _checkAuth(self, authToken):
        self.client = shimclient.ShimMintClient(self.cfg, authToken)
        return self.client.checkAuth()

    def _getHandler(self, cmd, auth):
        self.req.content_type = "application/xhtml+xml"

        fullHost = self.req.hostname
        hostname = fullHost.split('.')[0]
        
        if hostname == "www":
            self.project = None
        else:
            try:
                self.project = self.client.getProjectByHostname(fullHost)
            except database.ItemNotFound:
                return lambda auth: apache.HTTP_NOT_FOUND
        try:    
            method = self.__getattribute__(cmd)
        except AttributeError:
            if hostname == "www":
                method = self.frontPage
            else:
                method = self.projectPage
        return method

    def frontPage(self, auth):
        self._write("frontPage")
        return apache.OK

    def register(self, auth):
        self._write("register")
        return apache.OK

    @strFields(message = "")
    def login(self, auth, message):
        self._write("login", message = message)
        return apache.OK

    @strFields(username = None, password = None)
    def login2(self, auth, username, password):
        authToken = (username, password)
        client = shimclient.ShimMintClient(self.cfg, authToken)
        auth = client.checkAuth()
        
        if auth.passwordOK:
            return self._redirect("login?message=invalid")
        else:
            auth = base64.encodestring("%s:%s" % authToken).strip()
            cookie = Cookie.Cookie('authToken', auth)
            # we have to add the cookie headers manually, because mod_python
            # looks at err_headers_out instead of headers_out when doing a redirect.
            self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
            self.req.err_headers_out.add("Set-Cookie", str(cookie))
            return self._redirect("mainMenu")

    def projectPage(self, auth):    
        self._write("projectPage", project = self.project)
        return apache.OK

    def newProject(self, auth):
        self._write("newProject")
        return apache.OK

    def _write(self, template, **values):
        path = os.path.join(self.cfg.templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding="utf-8", cfg = self.cfg,
                                                auth = self.auth,
                                                **values)
        self.req.write(content) 

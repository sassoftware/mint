#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import base64
import os
import kid
import sys
import time

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

#import conary
from web import webhandler
from web.fields import strFields, intFields, listFields, boolFields

from mint import shimclient
from mint import projects
from mint import database
from mint import users
from mint import userlevels

class MintApp(webhandler.WebHandler):
    def _checkAuth(self, authToken):
        self.client = shimclient.ShimMintClient(self.cfg, authToken)
        auth = self.client.checkAuth()
        return auth

    def _404(self, *args, **kwargs):
        return apache.HTTP_NOT_FOUND 

    def _getHandler(self, cmd, auth):
        fullHost = self.req.hostname
        hostname = fullHost.split('.')[0]
        
        if hostname == "www":
            self.project = None
            default = self.frontPage
        else:
            try:
                self.project = self.client.getProjectByHostname(fullHost)
            except database.ItemNotFound:
                return self._404
            default = self.projectPage
        try:
            if not cmd:
               method = default
            else:
               method = self.__getattribute__(cmd)
        except AttributeError:
            return self._404
        return method

    def _methodHandler(self):
        self.user = None
        if 'authToken' in self.cookies:
            auth = base64.decodestring(self.cookies['authToken'].value)
            authToken = auth.split(":")

            auth = self._checkAuth(authToken)

            if not auth.authorized:
                self._clearAuth()
                return self._redirect("login")
            else:
                self.user = self.client.getUser(auth.userId)
        else:
            authToken = ('anonymous', 'anonymous')
            self._checkAuth(authToken)
            auth = users.Authorization()

        self.authToken = authToken
        self.auth = auth

        if self.cmd.startswith("_"):
            return apache.HTTP_NOT_FOUND

        method = self._getHandler(self.cmd, auth)

        d = dict(self.fields)
        d['auth'] = self.auth
        return method(**d)

    def _clearAuth(self):
        cookie = Cookie.Cookie('authToken', '', domain = self.cfg.domainName)
        cookie.expires = time.time() - 300
        self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
        self.req.err_headers_out.add("Set-Cookie", str(cookie))

    def frontPage(self, auth):
        self._write("frontPage")
        return apache.OK

    def register(self, auth):
        self._write("register")
        return apache.OK

    @strFields(username = None, email = None, password = None, password2 = None)
    def processRegister(self, auth, username, email, password, password2):
        if password != password2:
            self._write("error", shortError = "Registration Error",
                        error = "Passwords do not match.")
        elif len(password) < 6:
            self._write("error", shortError = "Registration Error",
                        error = "Password must be 6 characters or longer.")
        else:
            try:
                self.client.registerNewUser(username, password, username, email)
            except users.UserAlreadyExists:
                self._write("error", shortError = "Registration Error",
                            error = "An account with that username already exists.")
            else:
                return self._redirect("login")
        return apache.OK

    @strFields(message = "")
    def login(self, auth, message):
        self._write("login", message = message)
        return apache.OK

    def logout(self, auth):
        self._clearAuth()
        return self._redirect("login")

    @strFields(username = None, password = None)
    def login2(self, auth, username, password):
        authToken = (username, password)
        client = shimclient.ShimMintClient(self.cfg, authToken)
        auth = client.checkAuth()
        
        if not auth.authorized:
            return self._redirect("login?message=invalid")
        else:
            auth = base64.encodestring("%s:%s" % authToken).strip()
            cookie = Cookie.Cookie('authToken', auth, domain = self.cfg.domainName)
            
            # we have to add the cookie headers manually, because mod_python
            # looks at err_headers_out instead of headers_out when doing a redirect.
            self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
            self.req.err_headers_out.add("Set-Cookie", str(cookie))
            return self._redirect("frontPage")

    def confirm(self, id):
        try:
            self.client.confirmUser(id)
        except users.ConfirmError:
            self._write("error", shortError = "Confirm Failed",
                                    error = "Sorry, an error has occurred while confirming your registration.")
        except users.AlreadyConfirmed:
            self._write("error", shortError = "Already Confirmed",
                                    error = "Your account has already been confirmed.")
        else:
            return self._redirect("login?message=confirmed")
        return apache.OK 

    def projectPage(self, auth):    
        self._write("projectPage", project = self.project)
        return apache.OK

    def userSettings(self, auth):
        self._write("userSettings")
        return apache.OK

    @strFields(email = "", password1 = "", password2 = "")
    def editUserSettings(self, auth):
        if not email:
            email = auth.email
        
    def newProject(self, auth):
        self._write("newProject")
        return apache.OK

    @strFields(title = None, hostname = None)
    def createProject(self, auth, title, hostname):
        projectId = self.client.newProject(title, hostname)
        return self._redirect("http://%s.%s/" % (hostname, self.cfg.domainName) )

    def members(self, auth):
        self._write("members", project = self.project)
        return apache.OK

    @strFields(username = None)
    def editMembers(self, auth, username):
        self.project.addMemberByName(username, userlevels.DEVELOPER)
        return self._redirect("members")

    @intFields(id = None)
    def delMember(self, auth, id):
        self.project.delMemberById(id)
        return self._redirect("members")

    def _write(self, template, **values):
        path = os.path.join(self.cfg.templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding="utf-8", cfg = self.cfg,
                                                auth = self.auth,
                                                **values)
        self.req.write(content)

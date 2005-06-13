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

from web import webhandler
from web.fields import strFields, intFields, listFields, boolFields

from mint import shimclient
from mint import projects
from mint import database
from mint import users
from mint import userlevels
from mint import mint_error

def requiresAuth(func):
    def wrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise users.PermissionDenied
        else:
            return func(self, **kwargs)
    return wrapper

# decorates a method to be callable only by the owner of the current package
# also requires that a package exist
def ownerOnly(func):
    def wrapper(self, **kwargs):
        if not self.project:
            raise database.ItemNotFound("project")
        if self.userLevel == userlevels.OWNER:
            return func(self, **kwargs)
        else:
            raise users.PermissionDenied
    return wrapper

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
            self.userLevel = -1
            default = self.frontPage
        else:
            try:
                self.project = self.client.getProjectByHostname(fullHost)
                self.userLevel = self.project.getUserLevel(self.auth.userId)
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
        try:
            return method(**d)
        except mint_error.MintError, e:
            err_name = sys.exc_info()[0].__name__
            self.req.log_error("%s: %s" % (err_name, str(e)))
            self._write("error", shortError = err_name, error = str(e))
            return apache.OK

    def _redirCookie(self, cookie):
        # we have to add the cookie headers manually when redirecting, because 
        # mod_python looks at err_headers_out instead of headers_out.

        self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
        self.req.err_headers_out.add("Set-Cookie", str(cookie))

    def _clearAuth(self):
        cookie = Cookie.Cookie('authToken', '', domain = self.cfg.domainName,
                                                expires = time.time() - 300)
        self._redirCookie(cookie)
        
    def frontPage(self, auth):
        projectList = self.client.getProjectsByMember(auth.userId)
        self._write("frontPage", projectList = projectList)
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
                return self._redirect("login?message=confirm")
        return apache.OK

    @strFields(message = "")
    def login(self, auth, message):
        self._write("login", message = message)
        return apache.OK

    def logout(self, auth):
        self._clearAuth()
        return self._redirect("login")

    @strFields(username = None, password = '', submit = None)
    def login2(self, auth, username, password, submit):
        if submit == "Log In":
            authToken = (username, password)
            client = shimclient.ShimMintClient(self.cfg, authToken)
            auth = client.checkAuth()
            
            if not auth.authorized:
                return self._redirect("login?message=invalid")
            else:
                auth = base64.encodestring("%s:%s" % authToken).strip()
                cookie = Cookie.Cookie('authToken', auth, domain = self.cfg.domainName)
                self._redirCookie(cookie)
                return self._redirect("frontPage")
        elif submit == "Forgot Password":
            newpw = users.newPassword()
            
            userId = self.client.getUserIdByName(username)
            user = self.client.getUser(userId)
            user.setPassword(newpw)
            
            message = "\n".join(["Your password for rpath.com has been reset to:",
                                 "",
                                 "    %s" % newpw,
                                 "",
                                 "Please log in at http://www.rpath.com/ and change",
                                 "this password as soon as possible."])

            users.sendMail(self.cfg.adminMail, "rpath.com", user.getEmail(),
                           "rpath.com forgotten password", message)
        
    @strFields(id = None)
    def confirm(self, auth, id):
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
        self._write("projectPage")
        return apache.OK

    @requiresAuth
    def userSettings(self, auth):
        self._write("userSettings")
        return apache.OK

    @strFields(email = "", displayEmail = "", password1 = "", password2 = "")
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, password1, password2):
        #if email != auth.email:
        #    # XXX confirm valid email
        #    self.user.setEmail(email)
        if displayEmail != auth.displayEmail:
            self.user.setDisplayEmail(displayEmail)

        if password1 != password2:
            self._write("error", shortError = "Registration Error",
                        error = "Passwords do not match.")
        elif len(password1) < 6:
            self._write("error", shortError = "Registration Error",
                        error = "Password must be 6 characters or longer.")
        else:
            self.user.setPassword(password1)
            return self._redirect("logout")

        return self._redirect("frontPage")

    @requiresAuth
    def newProject(self, auth):
        self._write("newProject")
        return apache.OK

    @strFields(title = None, hostname = None)
    @requiresAuth
    def createProject(self, auth, title, hostname):
        projectId = self.client.newProject(title, hostname)
        return self._redirect("http://%s.%s/" % (hostname, self.cfg.domainName) )

    @requiresAuth
    @ownerOnly
    def projectDesc(self, auth):
        self._write("projectDesc")
        return apache.OK

    @strFields(desc = None)
    @requiresAuth
    @ownerOnly
    def editProjectDesc(self, auth, desc):
        self.project.setDesc(desc)
        return self._redirect("/")

    def members(self, auth):
        self._write("members")
        return apache.OK

    @strFields(username = None)
    @intFields(level = None)
    @requiresAuth
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        return self._redirect("members")

    @intFields(id = None)
    @requiresAuth
    @ownerOnly
    def delMember(self, auth, id):
        self.project.delMemberById(id)
        return self._redirect("members")

    @intFields(userId = None)
    @requiresAuth
    @ownerOnly
    def memberSettings(self, auth, userId):
        user, level = self.client.getMembership(userId, self.project.getId()) 
        self._write("memberSettings", user = user, otherUserLevel = level)
        return apache.OK

    @intFields(id = None)
    def userInfo(self, auth, id):
        user = self.client.getUser(id)
        self._write("userInfo", user = user,
            userProjects = self.client.getProjectsByUser(id))
        return apache.OK

    def _write(self, template, **values):
        path = os.path.join(self.cfg.templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding="utf-8", cfg = self.cfg,
                                                auth = self.auth,
                                                project = self.project,
                                                userLevel = self.userLevel,
                                                **values)
        self.req.write(content)

#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import base64
import os
import stat
import sys
import re
from urllib import quote, unquote

from mod_python import apache

import versions
from web import fields
from web.fields import strFields, intFields, listFields, boolFields

from mint import mint_error
from mint import projects
from mint import shimclient
from mint import users
from mint import userlevels
from mint import mailinglists

from webhandler import WebHandler, normPath
from decorators import requiresAdmin, requiresAuth
from decorators import mailList

class SiteHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)
            
        path = normPath(context['cmd'])
        cmd = path.split('/')[1]
       
        if not cmd:
            return self._frontPage
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            return self._404

        if self.auth.stagnant and cmd not in ['editUserSettings','confirm','logout']:
            return self.confirmEmail
        if not callable(method):
            method = self._404
        return method

    def _frontPage(self, auth):
        news = self.client.getNews()
        self._write("frontPage", news = news, newsLink = self.client.getNewsLink())
        return apache.OK
        
    def register(self, auth):
        self._write("register", errors=[], kwargs={})
        return apache.OK

    @strFields(username = '', email = '',
               password = '', password2 = '',
               fullName = '', displayEmail = '',
               blurb = '', tos='', privacy='')
    def processRegister(self, auth, username, 
                        fullName, email, password,
                        password2, displayEmail,
                        blurb, tos, privacy):
        errors = []
        if not username:
            errors.append("You must supply a username.")
        if not email:
            errors.append("You must supply a valid e-mail address.  This will be used to confirm your account.")
        if not password or not password2:
            errors.append("Password field left blank.")
        if password != password2:
            errors.append("Passwords do not match.")
        if len(password) < 6:
            errors.append("Password must be 6 characters or longer.")
        if not tos:
            errors.append("You must accept the Terms of Service to create an account")
        if not privacy:
            errors.append("You must accept the Privacy Policy to create an account")
        if not errors:
            try:
                self.client.registerNewUser(username, password, fullName, email,
                            displayEmail, blurb)
            except users.UserAlreadyExists:
                errors.append("An account with that username already exists.")
            except users.GroupAlreadyExists:
                errors.append("An account with that username already exists.")
            except users.MailError,e:
                errors.append(e.context);
        if not errors:
            self._write("register_conf", email = email)
        else:
            kwargs = {'username': username,
                      'email': email,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb,
                      'tos': tos,
                      'privacy': privacy}
            self._write("register", errors=errors, kwargs = kwargs)
        return apache.OK

    def confirmEmail(self, auth, **kwargs):
        self._write("confirmEmail", email=auth.email)
        return apache.OK

    @strFields(page = None)
    def legal(self, auth, page):
        if page not in ["tos", "privacy"]:
            return apache.HTTP_NOT_FOUND
            
        self._write(page)
        return apache.OK

    @strFields(message = "")
    def login(self, auth, message):
        self.toUrl = "/"
        self._write("login", message = message)
        return apache.OK

    def logout(self, auth):
        self._clearAuth()
        return self._redirect("/")

    def _resetPassword(self, username):
        userId = self.client.getUserIdByName(username)
        user = self.client.getUser(userId)
        self._resetPasswordById(userId)
        self._write("forgotPassword", email = user.getEmail())
        return apache.OK

    @strFields(username = None, password = '', submit = None, to = '/')
    def processLogin(self, auth, username, password, submit, to):
        if submit == "Log In":
            authToken = (username, password)
            client = shimclient.ShimMintClient(self.cfg, authToken)
            auth = client.checkAuth()

            if not auth.authorized:
                raise mint_error.InvalidLogin
            else:
                client.updateAccessedTime(auth.userId)
                self.session['authToken'] = authToken
                
                # mod_python's cookie classes don't handle 301 redirects because
                # Cookie.add_cookie only adds cookie headers to req.headers_out,
                # not req_error_headers_out, which is used for redirects,
                # so we have to manually add the cookie to the right headers
                # table.
                c = self.session.make_cookie()
                self.req.err_headers_out.add('Set-Cookie', str(c))
                self.req.err_headers_out.add('Cache-Control', 'no-cache="set-cookie"')
                
                self.session.save()
                return self._redirect(unquote(to))
                
        elif submit == "Forgot Password":
            return self._resetPassword(username)
        else:
            return apache.HTTP_NOT_FOUND

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
            if auth.authorized:
                return self._redirect("/")
            else:
                self._write("register_active")
        return apache.OK 

    @intFields(sortOrder = 0, limit = 10, offset = 0)
    def projects(self, auth, sortOrder, limit, offset, submit = 0):
        results, count = self.client.getProjects(sortOrder, limit, offset)
        self._write("projects", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)
        return apache.OK

    @requiresAdmin
    @intFields(sortOrder = 0, limit = 10, offset = 0)
    def users(self, auth, sortOrder, limit, offset, submit = 0):
        results, count = self.client.getUsers(sortOrder, limit, offset)
        self._write("users", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)
        return apache.OK

    @requiresAuth
    def userSettings(self, auth):
        self._write("userSettings")
        return apache.OK

    @strFields(email = "", displayEmail = "",
               password1 = "", password2 = "",
               fullName = "", blurb = "")
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, fullName,
                         password1, password2, blurb):
        if email != auth.email:
            self.user.validateNewEmail(email)
            self.user.setEmail(email)
            self._clearAuth()
            self._write("register_reconf", email = email)
            return apache.OK

        if displayEmail != auth.displayEmail:
            self.user.setDisplayEmail(displayEmail)
        if blurb != auth.blurb:
            self.user.setBlurb(blurb)
        if fullName != auth.fullName:
            self.user.setFullName(fullName)

        if password1 and password2:
            if password1 != password2:
                self._write("error", shortError = "Registration Error",
                            error = "Passwords do not match.")
            elif len(password1) < 6:
                self._write("error", shortError = "Registration Error",
                            error = "Password must be 6 characters or longer.")
            else:
                self.user.setPassword(password1)
                return self._redirect("logout")

        return self._redirect("/")

    @requiresAuth
    @listFields(str, projects=[])
    @strFields(keydata = '')
    def uploadKey(self, auth, projects, keydata):
        if self.projectList:
            self._write("uploadKey", errors=[], kwargs={})
        else:
            self._write("error", shortError="Not a project member", error="You may not upload a key as you are not a member of any projects.  Create a project, or ask a project owner to add you to their project and then come back")
        return apache.OK

    @requiresAuth
    @listFields(str, projects=None)
    @strFields(keydata=None)
    def processKey(self, auth, projects, keydata):
        for project, level in self.projectList:
            if project.getHostname() in projects:
                try:
                    project.addUserKey(auth.username, keydata)
                except Exception, e:
                    self._write("uploadKey", errors = ['Error uploading key: %s' % str(e)], 
                            kwargs={'projects': projects, 'keydata': keydata})
                    return apache.OK
        return self._redirect("/")
        
    @requiresAuth
    def newProject(self, auth):
        self._write("newProject", errors=[], kwargs={})
        return apache.OK

    @mailList
    def _createProjectLists(self, mlists, auth, projectName, optlists = []):
        lists = mailinglists.GetLists(projectName, optlists)
        lists.update(mailinglists.GetLists(projectName, mailinglists.defaultlists))
        success = True
        error = False
        for name, values in lists.items():
            success = mlists.add_list(self.cfg.MailListPass, name, '', values['description'], auth.email, True, values['moderate'])
            if not success: error = False
        return not error

    @strFields(title = '', hostname = '', projecturl = '', blurb = '')
    @listFields(int, optlists = [])
    @requiresAuth
    def createProject(self, auth, title, hostname, projecturl, blurb, optlists):
        hostname = hostname.lower()
        errors = []
        if not title:
            error.append("You must supply a project title")
        if not hostname:
            error.append("You must supply a project hostname")
        if not errors:
            try:
                #attempt to create the project
                projectId = self.client.newProject(title, hostname, 
                                self.cfg.domainName, projecturl, blurb)
                #Now create the mailing lists
                if self.cfg.EnableMailLists and not errors:
                    if not self._createProjectLists(auth=auth, 
                                                    projectName=hostname,
                                                    optlists=optlists):
                        raise mailinglists.MailingListException("Could not create the mailing lists, check the mailing list page to set up your desired lists.")
            except mailinglists.MailingListException:
                raise
            except projects.DuplicateHostname, e:
                errors.append(str(e))
            except projects.DuplicateName, e:
                errors.append(str(e))
            except mint_error.MintError, e:
                errors.append(str(e))
        if not errors:
            return self._redirect("http://%s/project/%s/" % (self.siteHost, hostname))
        else:
            kwargs = {'title': title, 'hostname': hostname, 'projecturl': projecturl, 'blurb': blurb, 'optlists': optlists}
            self._write("newProject", errors=errors, kwargs=kwargs)
            return apache.OK

    @intFields(userId = None, projectId = None, level = None)
    def addMemberById(self, auth, userId, projectId, level):
        project = self.client.getProject(projectId)
   
        if project.getUserLevel(auth.userId) != userlevels.OWNER:
            raise mint_error.PermissionDenied
    
        project.addMemberById(userId, level)
        return self._redirect("http://%s" % project.getFQDN())

    @intFields(id = None)
    def userInfo(self, auth, id):
        user = self.client.getUser(id)
        self._write("userInfo", user = user,
            userProjects = self.client.getProjectsByMember(id))
        return apache.OK

    @strFields(search = "", type = None)
    @intFields(limit = 10, offset = 0, modified = 0)
    def search(self, auth, type, search, modified, limit, offset):
        if type == "Projects" and auth.admin:
            return self._projectSearch(search, modified, limit, offset)
        elif type == "Users" and auth.admin:
            return self._userSearch(auth, search, limit, offset)
        elif type == "Packages":
            return self._packageSearch(search, limit, offset)
        else:
            self._write("error", shortError = "Invalid Search Type",
                error = "Invalid search type specified.")
            return apache.OK

    def _userSearch(self, auth, terms, limit, offset):
        results, count = self.client.getUserSearchResults(terms, limit, offset)
        self._write("searchResults", searchType = "Users", terms = terms, results = results,
                                     count = count, limit = limit, offset = offset,
                                     modified = 0)
        return apache.OK

    def _packageSearch(self, terms, limit, offset):
        results, count = self.client.getPackageSearchResults(terms, limit, offset)

        searchResults = []
        for x in results:
            if x[2]:
                p = self.client.getProject(x[2])
                name = p.getName()
                host = p.getHostname()
                reposUrl = '/project/%s/' % host
                packageUrl = '/repos/%s/troveInfo?t=%s' % (host, x[0])
            else:
                version = versions.VersionFromString(x[1])
                name = version.branch().label().getHost()
                host = name
                reposUrl = 'http://%s/conary/' % host
                packageUrl = reposUrl + "troveInfo?t=%s" % x[0]
                reposUrl += 'browse'
            searchResults.append( (x[0], x[1], packageUrl, name, reposUrl) )
            
        self._write("searchResults", searchType = "Packages", terms = terms, results = searchResults,
                                     count = count, limit = limit, offset = offset,
                                     modified = 0)
        return apache.OK
    
    def _projectSearch(self, terms, modified, limit, offset):
        results, count = self.client.getProjectSearchResults(terms, modified, limit, offset)
        self._write("searchResults", searchType = "Projects", terms = terms, results = results,
                                     count = count, limit = limit, offset = offset,
                                     modified = modified)
        return apache.OK

    @intFields(fileId = None)
    def downloadImage(self, auth, fileId):
        filename = self.client.getFilename(fileId)

        try:
            size = os.stat(filename)[stat.ST_SIZE]

            self.req.content_type = "application/octet-stream"
            self.req.headers_out["Content-Disposition"] = "attachment; filename=%s;" %\
                os.path.basename(filename)
            self.req.headers_out["Content-Length"] = str(size)
            self.req.sendfile(filename)
        except OSError, e:
            self._write("error", shortError = "File error",
                        error = "An error has occurred opening the image file: %s" % e)
        return apache.OK

    @requiresAuth
    @boolFields(confirmed = False)
    def cancelAccount(self, auth, confirmed):
        if confirmed:
            #do the actual deletion
            self.user.cancelUserAccount()
            self._clearAuth()
            return self._redirect("/")
        else:
            self._write("confirm", message = "Are you sure you want to delete your account?",
                yesLink = "cancelAccount?confirmed=1",
                noLink = "/")
        return apache.OK

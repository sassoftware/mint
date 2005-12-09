#
# Copyright (c) 2005 rPath, Inc.
#
# All rights reserved
#
import base64
import email
import os
import stat
import sys
import re
from urllib import quote, unquote, quote_plus

from mod_python import apache

import conary.versions
from conary.web.fields import strFields, intFields, listFields, boolFields

from mint import mint_error
from mint import projects
from mint import shimclient
from mint import users
from mint import userlevels
from mint import mailinglists
from mint import projectlisting
from mint import database
from mint.session import SqlSession

from webhandler import WebHandler, normPath, HttpNotFound, HttpPartialContent
from decorators import requiresAdmin, requiresAuth, requiresHttps, redirectHttps, redirectHttp
from decorators import mailList
from cache import cache

class SiteHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        # if someone attempts to access the SITE from something other than
        # the site host and SSL is not requested, redirect.
        if self.req.hostname != self.cfg.siteHost.split(':')[0] and self.req.subprocess_env.get('HTTPS', 'off') == 'off':
            self.req.log_error("%s %s accessed incorrectly; referer: %s" % \
                (self.req.hostname, self.req.unparsed_uri, self.req.headers_in.get('referer', 'N/A')))
            self._redirect("http://" + self.cfg.siteHost + self.req.unparsed_uri)
        if not cmd:
            return self._frontPage
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound

        if not callable(method):
            raise HttpNotFound

        return method

    @cache
    @redirectHttp
    def _frontPage(self, auth):
        news = self.client.getNews()
        releases = self.client.getReleaseList()
        return self._write("frontPage", news = news, newsLink = self.client.getNewsLink(), firstTime=self.session.get('firstTimer', False), releases=releases)
        
    def blank(self, auth, sid, hostname):
        self.req.content_type = "image/gif"

        # 1x1 transparent gif
        return 'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\xff\xff\xff!'\
               '\xf9\x04\x01\n\x00\x01\x00,\x00\x00\x00\x00\x01\x00\x01\x00'\
               '\x00\x02\x02L\x01\x00;'
        
    @redirectHttps
    def register(self, auth):
        self.toUrl = self.cfg.basePath
        return self._write("register", errors=[], kwargs={})

    @strFields(username = '', email = '',
               password = '', password2 = '',
               fullName = '', displayEmail = '',
               blurb = '', tos='', privacy='')
    @requiresHttps
    def processRegister(self, auth, username, 
                        fullName, email, password,
                        password2, displayEmail,
                        blurb, tos, privacy):
        self.toUrl = self.cfg.basePath

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
            self._redirectHttp('registerComplete')
        else:
            kwargs = {'username': username,
                      'email': email,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb,
                      'tos': tos,
                      'privacy': privacy}
            return self._write("register", errors=errors, kwargs = kwargs)

    def registerComplete(self, auth):
        self.toUrl = self.cfg.basePath
        return self._write("register_conf")

    @redirectHttps
    def confirmEmail(self, auth, **kwargs):
        return self._write("confirmEmail", email=auth.email)

    @strFields(page = None)
    def legal(self, auth, page):
        try:
            return self._write("docs/" + page)
        except IOError:
            raise HttpNotFound

    @strFields(message = "")
    @redirectHttps
    def forgotPassword(self, auth, message):
        self.toUrl = self.cfg.basePath
        return self._write("forgotPassword", message = message)

    @redirectHttp
    @strFields(page = "")
    @intFields(step = 1)
    def help(self, auth, page, step):
        if page:
            try:
                return self._write("docs/" + page, step = step)
            except IOError:
                return self._write("docs/overview")
        else:
            return self._write("docs/overview")

    def logout(self, auth):
        self._clearAuth()
        self._redirect(self.cfg.basePath)

    @requiresHttps
    @strFields(username = None)
    def resetPassword(self, auth, username):
        self.toUrl = self.cfg.basePath
        userId = self.client.getUserIdByName(username)
        user = self.client.getUser(userId)
        self._resetPasswordById(userId)
        
        return self._write("passwordReset", email = user.getEmail())

    @requiresHttps
    @strFields(username = None, password = '', action = 'login', to = '/')
    def processLogin(self, auth, username, password, action, to):
        if action == 'login':
            authToken = (username, password)
            client = shimclient.ShimMintClient(self.cfg, authToken)
            auth = client.checkAuth()

            if not auth.authorized:
                raise mint_error.InvalidLogin
            else:
                if auth.timeAccessed > 0:
                    firstTimer = False
                else:
                    firstTimer = True
                client.updateAccessedTime(auth.userId)

                self._session_start()
                self.session['authToken'] = authToken
                self.session['firstTimer'] = firstTimer
                self.session.save()

                self._redirect_storm(self.session.id())
                self._redirect(unquote(to)) 
        else:
            raise HttpNotFound

    @strFields(id = None)
    def confirm(self, auth, id):
        self.toUrl = self.cfg.basePath 
        try:
            self.client.confirmUser(id)
        except users.ConfirmError:
            return self._write("error", shortError = "Confirm Failed",
                error = "Sorry, an error has occurred while confirming your registration.")
        except users.AlreadyConfirmed:
            return self._write("error", shortError = "Already Confirmed",
                error = "Your account has already been confirmed.")
        else:
            if auth.authorized:
                self._redirect(self.cfg.basePath)
            else:
                return self._write("register_active")

    @intFields(sortOrder = -1, limit = 10, offset = 0)
    def projects(self, auth, sortOrder, limit, offset, submit = 0):
        if sortOrder < 0:
            sortOrder = self.session.get('projectsSortOrder', 0)
        self.session['projectsSortOrder'] = sortOrder
        results, count = self.client.getProjects(sortOrder, limit, offset)
        for i, x in enumerate(results[:]):
            results[i][0] = self.client.getProject(x[0])

        return self._write("projects", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)

    @requiresAdmin
    @intFields(sortOrder = -1, limit = 10, offset = 0)
    def users(self, auth, sortOrder, limit, offset, submit = 0):
        if sortOrder < 0:
            sortOrder = self.session.get('usersSortOrder', 0)
        self.session['usersSortOrder'] = sortOrder
        results, count = self.client.getUsers(sortOrder, limit, offset)
        
        return self._write("users", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)

    @requiresAuth
    @redirectHttps
    def userSettings(self, auth):
        return self._write("userSettings")

    @strFields(email = "", displayEmail = "",
               password1 = "", password2 = "",
               fullName = "", blurb = "")
    @requiresHttps
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, fullName,
                         password1, password2, blurb):
        if email != auth.email:
            self.user.validateNewEmail(email)
            self.user.setEmail(email)
            self._clearAuth()
            return self._write("register_reconf", email = email)

        if displayEmail != auth.displayEmail:
            self.user.setDisplayEmail(displayEmail)
        if blurb != auth.blurb:
            self.user.setBlurb(blurb)
        if fullName != auth.fullName:
            self.user.setFullName(fullName)

        if password1 and password2:
            if password1 != password2:
                return self._write("error", shortError = "Registration Error",
                            error = "Passwords do not match.")
            elif len(password1) < 6:
                return self._write("error", shortError = "Registration Error",
                            error = "Password must be 6 characters or longer.")
            else:
                self.user.setPassword(password1)
                self._redirectHttp("logout")

        self._redirectHttp('/')

    @requiresAuth
    @listFields(str, projects=[])
    @strFields(keydata = '')
    def uploadKey(self, auth, projects, keydata):
        if self.projectList:
            return self._write("uploadKey", errors=[], kwargs={})
        else:
            return self._write("error", shortError="Not a project member",
                error = "You may not upload a key as you are not a member of any projects. "
                        "Create a project, or ask a project owner to add you to their "
                        "project and then come back")

    @requiresAuth
    @listFields(str, projects=None)
    @strFields(keydata=None)
    def processKey(self, auth, projects, keydata):
        for project, level in self.projectList:
            if project.getHostname() in projects:
                try:
                    project.addUserKey(auth.username, keydata)
                except Exception, e:
                    return self._write("uploadKey", errors = ['Error uploading key: %s' % str(e)], 
                            kwargs={'projects': projects, 'keydata': keydata})
        self._redirect(self.cfg.basePath)
        
    @requiresAuth
    def newProject(self, auth):
        return self._write("newProject", errors=[], kwargs={})

    @mailList
    def _createProjectLists(self, mlists, auth, projectName, optlists = []):
        #Get the formatted list of optional lists
        lists = mailinglists.GetLists(projectName, optlists)
        #Get the formatted list of default lists and add them to "lists"
        lists.update(mailinglists.GetLists(projectName, mailinglists.defaultlists))
        success = True
        error = False
        for name, values in lists.items():
            # Create the lists
            success = mlists.add_list(self.cfg.MailListPass, name, '', values['description'], auth.email, True, values['moderate'])
            if not success: error = False
        #add the commits sender address
        mlists._servercall(
            mlists.server.set_list_settings(
                mailinglists.listnames[mailinglists.PROJECT_COMMITS]%projectName,
                self.cfg.MailListPass,
                {'accept_these_nonmembers': self.cfg.commitEmail }
            )
        )
        return not error

    @strFields(title = '', hostname = '', projecturl = '', blurb = '')
    @listFields(int, optlists = [])
    @requiresAuth
    def createProject(self, auth, title, hostname, projecturl, blurb, optlists):
        hostname = hostname.lower()
        errors = []
        if not title:
            errors.append("You must supply a project title")
        if not hostname:
            errors.append("You must supply a project hostname")
        if not errors:
            try:
                # attempt to create the project
                projectId = self.client.newProject(title, hostname, 
                    self.cfg.projectDomainName, projecturl, blurb)
                # now create the mailing lists
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
            self._redirect("http://%s%s/project/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname))
        else:
            kwargs = {'title': title, 'hostname': hostname, 'projecturl': projecturl, 'blurb': blurb, 'optlists': optlists}
            return self._write("newProject", errors=errors, kwargs=kwargs)

    @intFields(userId = None, projectId = None, level = None)
    def addMemberById(self, auth, userId, projectId, level):
        project = self.client.getProject(projectId)
   
        if project.getUserLevel(auth.userId) != userlevels.OWNER:
            raise mint_error.PermissionDenied
    
        project.addMemberById(userId, level)
        self._redirect("%sproject/%s" % (self.cfg.basePath, project.getHostname()))

    @intFields(id = None)
    @requiresAuth
    def userInfo(self, auth, id):
        user = self.client.getUser(id)
        if user.active or auth.admin:
            userProjects = []
            if auth.userId == id:
                #Show all the projects.  The user is viewing his own profile
                userProjects = [x for x in self.client.getProjectsByMember(id)]
            else:
                for x in self.client.getProjectsByMember(id):
                    if x[0].hidden and (x[0].getUserLevel(auth.userId) == userlevels.NONMEMBER):
                        if not auth.admin:
                            #Skip this project, it's hidden and the user requesting is
                            #not a member the project
                            continue
                    userProjects.append(x)
            return self._write("userInfo", user = user, userProjects = userProjects)
        else:
            raise database.ItemNotFound('userid')

    @strFields(search = "", type = None)
    @intFields(limit = 10, offset = 0, modified = 0)
    def search(self, auth, type, search, modified, limit, offset):
        self.session['searchType'] = type
        if type == "Projects":
            return self._projectSearch(search, modified, limit, offset)
        elif type == "Users" and auth.authorized:
            return self._userSearch(auth, search, limit, offset)
        elif type == "Packages":
            return self._packageSearch(search, limit, offset)
        else:
            self.session['searchType'] = ''
            return self._write("error", shortError = "Invalid Search Type",
                error = "Invalid search type specified.")

    def _userSearch(self, auth, terms, limit, offset):
        results, count = self.client.getUserSearchResults(terms, limit, offset)
        return self._write("searchResults", searchType = "Users", terms = terms, results = results,
                                            count = count, limit = limit, offset = offset, modified = 0)

    def _packageSearch(self, terms, limit, offset):
        results, count = self.client.getPackageSearchResults(terms, limit, offset)

        searchResults = []
        for x in results:
            p = self.client.getProject(x[2])
            host = p.getHostname()
            reposUrl = '/project/%s/' % host
            packageUrl = '/repos/%s/troveInfo?t=%s' % (host, quote_plus(x[0]))
            searchResults.append( (x[0], x[1], packageUrl, p.getName(), reposUrl) )
            
        return self._write("searchResults", searchType = "Packages", terms = terms, results = searchResults,
                                            count = count, limit = limit, offset = offset, modified = 0)
    
    def _projectSearch(self, terms, modified, limit, offset):
        results, count = self.client.getProjectSearchResults(terms, modified, limit, offset)
        for i, x in enumerate(results[:]):
            results[i][0] = self.client.getProject(x[0])

        return self._write("searchResults", searchType = "Projects", terms = terms, results = results,
                                            count = count, limit = limit, offset = offset, modified = modified)

    @intFields(fileId = 0)
    def downloadImage(self, auth, fileId):
        reqFilename = None
        if not fileId:
            cmds = self.cmd.split('/')
            fileId = int(cmds[1])
            reqFilename = cmds[2]

        releaseId, idx, filename, title = self.client.getFileInfo(fileId)
        if reqFilename and os.path.basename(filename) != reqFilename:
            raise HttpNotFound

        # only count downloads of the first ISO
        if idx == 0:
            release = self.client.getRelease(releaseId)
            release.incDownloads()
        try:
            size = os.stat(filename)[stat.ST_SIZE]

            self.req.content_type = "application/octet-stream"
            self.req.headers_out["Content-Disposition"] = "attachment; filename=%s;" %\
                os.path.basename(filename)
            self.req.headers_out["Content-Length"] = str(size)

            # XXX this doesn't work yet
            # handle requests for partial content
            #if 'Range' in self.req.headers_in:
            #    # only support a specific syntax of Range
            #    m = re.match('bytes=(\d+)-', self.req.headers_in['Range'])
            #    if m:
            #        startByte = int(m.groups()[0])
            #        self.req.sendfile(filename, startByte)
            #        raise HttpPartialContent
                    
            self.req.sendfile(filename)
        except OSError, e:
            return self._write("error", shortError = "File error",
                error = "An error has occurred opening the image file: %s" % e)

    @requiresAuth
    @boolFields(confirmed = False)
    def cancelAccount(self, auth, confirmed):
        if confirmed:
            #do the actual deletion
            self.user.cancelUserAccount()
            self._clearAuth()
            self._redirect(self.cfg.basePath)
        else:
            return self._write("confirm", message = "Are you sure you want to delete your account?",
                yesLink = "cancelAccount?confirmed=1", noLink = self.cfg.basePath)

    @strFields(feed = 'newProjects')
    def rss(self, auth, feed):
        if feed == "newProjects":
            results, count = self.client.getProjects(projectlisting.CREATED_DES, 10, 0)
            
            title = "New %s Projects" % self.cfg.productName
            link = "http://%s%srss?feed=newProjects" % (self.cfg.siteHost, self.cfg.basePath)
            desc = "New projects created on %s" % self.cfg.productName

            items = []
            for p in results:
                item = {}
                project = self.client.getProject(p[0])
                
                item['title'] = project.getName()
                item['link'] = project.getUrl()
                item['content'] = "<p>A new project named <a href=\"%s\">%s</a> has been created.</p>" % \
                    (project.getUrl(), project.getName())
                item['content'] += "<blockquote>%s</blockquote>" % project.getDesc()
                item['date_822'] = email.Utils.formatdate(project.getTimeCreated())
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)
        elif feed == "newReleases":
            results = self.client.getReleaseList()
            title = "New releases on %s" % self.cfg.productName
            link = "http://%s%srss?feed=newReleases" % (self.cfg.siteHost, self.cfg.basePath)
            desc = "New releases published at %s" % self.cfg.productName

            items = []
            for p in results:
                item = {}
                release = p[2]
                item['title'] = p[0]
                item['link'] = 'http://%s%sproject/%s/release?id=%d' % (self.cfg.projectSiteHost, self.cfg.basePath, p[1], release.getId())
                item['content'] = "<p>A new release has been published by the <a href=\"http://%s%sproject/%s\">%s</a> project.</p>\n" % (self.cfg.projectSiteHost, self.cfg.basePath, p[1], p[0])
                item['content'] += "<p><a href=\"http://%s%sproject/%s/release?id=%d\">" % (self.cfg.projectSiteHost, self.cfg.basePath, p[1], release.getId())
                item['content'] += "%s=%s (%s)</a></p>" % (release.getTroveName(), release.getTroveVersion().trailingRevision().asString(), release.getArch())

                item['date_822'] = email.Utils.formatdate(release.timePublished)
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)

        return self._writeRss(items = items, title = title, link = link, desc = desc)

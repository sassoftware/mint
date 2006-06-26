#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All rights reserved
#
import base64
import email
import os
import stat
import sys
import re
from urllib import quote, unquote, quote_plus, urlencode

from mod_python import apache

from mint import database
from mint import data
from mint import mint_error
from mint import maintenance
from mint import mailinglists
from mint import projects
from mint import projectlisting
from mint import shimclient
from mint import users
from mint import userlevels
from mint.session import SqlSession

from mint.web.cache import cache
from mint.web.decorators import mailList, requiresAdmin, requiresAuth, \
     requiresHttps, redirectHttps, redirectHttp
from mint.web.webhandler import WebHandler, normPath, HttpNotFound, \
     HttpPartialContent, HttpOK

import conary.versions
from conary.web.fields import boolFields, dictFields, intFields, listFields, strFields

from rmake.build import buildjob

class SiteHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        # if someone attempts to access the SITE from something other than
        # the site host and SSL is not requested, redirect.
        # Notable exception: we will allow continueLogout to be accessed
        # on both domains.
        if self.req.hostname != self.cfg.siteHost.split(':')[0] and \
                self.req.subprocess_env.get('HTTPS', 'off') == 'off':
            self._redirect("http://" + self.cfg.siteHost + \
                           self.req.unparsed_uri)
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
    def _frontPage(self, auth, *args, **kwargs):
        popularProjects, _ = self.client.getProjects(projectlisting.NUMDEVELOPERS_DES, 10, 0)
        selectionData  = self.client.getFrontPageSelection()
        activeProjects, _  = self.client.getProjects(projectlisting.ACTIVITY_DES, 10, 0)
        spotlightData = self.client.getCurrentSpotlight()
        releases = self.client.getReleaseList()

        return self._write("frontPage", firstTime=self.session.get('firstTimer', False), popularProjects=popularProjects, selectionData = selectionData, activeProjects = activeProjects, spotlightData=spotlightData, releases=releases)

    def applianceSpotlight(self, *args, **kwargs):
        return self._write("applianceSpotlight", 
                    data=self.client.getSpotlightAll()) 
    @redirectHttps
    def register(self, auth):
        self.toUrl = self.cfg.basePath
        return self._write("register", errors=[], kwargs={})

    @strFields(newUsername = '', email = '', email2 = '',
               password = '', password2 = '',
               fullName = '', displayEmail = '',
               blurb = '', tos='', privacy='')
    @requiresHttps
    def processRegister(self, auth, newUsername,
                        fullName, email, email2, password,
                        password2, displayEmail,
                        blurb, tos, privacy):
        # newUsername only used to prevent browser value caching.
        username = newUsername
        self.toUrl = self.cfg.basePath

        errors = []
        if not username:
            errors.append("You must supply a username.")
        if not email or not email2:
            errors.append("You must supply a valid e-mail address.  This will be used to confirm your account.")
        if email != email2:
            errors.append("Email fields do not match.")
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
                      'email2': email2,
                      'fullName': fullName,
                      'displayEmail': displayEmail,
                      'blurb': blurb,
                      'tos': tos,
                      'privacy': privacy}
            return self._write("register", errors = errors, kwargs = kwargs)

    def registerComplete(self, auth):
        self.toUrl = self.cfg.basePath
        return self._write("register_conf")

    @redirectHttps
    def confirmEmail(self, auth, **kwargs):
        return self._write("confirmEmail", email=auth.email)

    @strFields(page = 'legal')
    def legal(self, auth, page):
        if not helpDocument(page):
            raise HttpNotFound
        return self._write("docs/" + page)

    @strFields(message = "")
    @redirectHttps
    def forgotPassword(self, auth, message):
        self.toUrl = self.cfg.basePath
        return self._write("forgotPassword", message = message)

    @redirectHttp
    @strFields(page = "")
    @intFields(step = 1)
    def help(self, auth, page, step):
        if not helpDocument(page):
            return self._write("docs/overview")
        return self._write("docs/" + page, step = step)

    @redirectHttps
    def logout(self, auth):
        self.session['visited'] = { }
        self.session['visited'][self.req.hostname] = True
        nexthop = self._getNextHop()
        if nexthop and isinstance(self.session, SqlSession):
            c = self.session.make_cookie()
            c.expires = 0
            self.req.err_headers_out.add('Set-Cookie', str(c))
            self.req.err_headers_out.add('Cache-Control', 
                    'no-cache="set-cookie"')
            self._redirect("http://%s%scontinueLogout" % \
                    (nexthop, self.cfg.basePath))
        else:
            self._clearAuth()
            self._redirect("http://%s%s" % \
                    (self.cfg.siteHost, self.cfg.basePath))

    def continueLogout(self, auth):
        self._clearAuth()
        self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))

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
    @boolFields(rememberMe = False)
    @intFields(x = 0, y = 0)
    def processLogin(self, auth, username, password, action, to, rememberMe,
                     x, y):
        if action == 'login':
            authToken = (username, password)
            client = shimclient.ShimMintClient(self.cfg, authToken)
            auth = client.checkAuth()

            maintenance.enforceMaintenanceMode(self.cfg, auth)

            if not auth.authorized:
                raise mint_error.InvalidLogin
            else:
                if auth.timeAccessed > 0:
                    firstTimer = False
                else:
                    firstTimer = True
                client.updateAccessedTime(auth.userId)

                self._session_start(rememberMe)
                self.session['authToken'] = authToken
                self.session['firstTimer'] = firstTimer
                self.session['firstPage'] = unquote(to)
                user = client.getUser(auth.userId)
                if user.getDefaultedData():
                    self.session['firstPage'] = self.cfg.basePath + "userSettings"
                self.session.save()

                # redirect storm if needed
                nexthop = self._getNextHop()
                prefix = 'http%s://' % (self.cfg.SSL and 's' or '')
                if nexthop:
                    self._redirect('%s%s%svalidateSession?%s' % (prefix, self.req.headers_in['Host'], self.cfg.basePath, urlencode((('nextHop', "http://%s%scontinueLogin?sid=%s" % (nexthop, self.cfg.basePath, self.session.id())),))))
                else:
                    self._redirect('%s%s%svalidateSession?%s' % (prefix, self.req.headers_in['Host'], self.cfg.basePath, urlencode((('nextHop', self.session['firstPage']),))))

        else:
            raise HttpNotFound

    def continueLogin(self, auth, sid = None):
        if sid:
            self._session_start()
            self._redirect('http://%s%svalidateSession?%s' % (self.req.headers_in['Host'], self.cfg.basePath, urlencode((('nextHop', self.session['firstPage']),))))
        else:
            raise HttpNotFound

    def validateSession(self, auth, nextHop):
        nextHop = unquote(nextHop)
        if type(self.session) is dict:
            if 'continueLogin' in nextHop or \
                   self.cfg.siteDomainName.split(':')[0] == \
                   self.cfg.projectDomainName.split(':')[0]:
                return self._write('error', shortError = "Login Failed",
                                   error = 'You cannot log in because your browser is blocking cookies to this site.')
            else:
                # the only time we ever need to redirect is if we're not on the
                # secure host. secure host is first of two hops.
                prefix = 'http%s://' % (self.cfg.SSL and 's' or '')
                self._redirect("%s%s%sloginFailed" % \
                               (prefix, self.cfg.secureHost,
                                self.cfg.basePath))
        else:
            self._redirect(nextHop)

    def loginFailed(self, auth):
        c = self.session.make_cookie()
        c.expires = 0
        self.req.err_headers_out.add('Set-Cookie', str(c))
        self.req.err_headers_out.add('Cache-Control',
                                     'no-cache="set-cookie"')
        return self._write('error', shortError = "Login Failed",
                           error = 'You cannot log in because your browser is blocking cookies to this site.')

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
                self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))
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

        results = [[x[0], x[1], x[2].encode('utf-8'), x[3].encode('utf-8'), x[4]] for x in results]
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
        return self._write("userSettings",
                           user = self.user,
                           dataDict = self.user.getDataDict(),
                           defaultedData = self.user.getDefaultedData())

    @strFields(email = "", displayEmail = "",
               password1 = "", password2 = "",
               fullName = "", blurb = "")
    @requiresHttps
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, fullName,
                         password1, password2, blurb, **kwargs):
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

        for key, (dType, default, prompt) in \
                self.user.getDataTemplate().iteritems():
            if dType == data.RDT_BOOL:
                val = bool(kwargs.get(key, False))
            elif dType == data.RDT_INT:
                val = int(kwargs.get(key, default))
            else:
                val = str(kwargs.get(key, default))
            self.user.setDataValue(key, val)

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
            return self._write("uploadKey", kwargs={})
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
                    self._addErrors('Error uploading key: %s' % str(e))
                    return self._write("uploadKey",
                            kwargs={'projects': projects, 'keydata': keydata})
        self._setInfo("Added key to project %s" % project.getNameForDisplay())
        self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))

    @requiresAuth
    def newProject(self, auth):
        return self._write("newProject", errors=[], kwargs={'domainname': self.cfg.projectDomainName.split(':')[0]})

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
        try:
            mlists.server.Mailman.setOptions(
                    mailinglists.listnames[mailinglists.PROJECT_COMMITS]%projectName,
                    self.cfg.MailListPass,
                    {'accept_these_nonmembers': self.cfg.commitEmail }
                )
        except: 
            mailinglists.MailingListException("Mailing List Error")
        return not error

    @strFields(title = '', hostname = '', domainname = '', projecturl = '', blurb = '')
    @listFields(int, optlists = [])
    @requiresAuth
    def createProject(self, auth, title, hostname, domainname, projecturl, blurb, optlists):
        hostname = hostname.lower()
        if not title:
            self._addErrors("You must supply a project title")
        if not hostname:
            self._addErrors("You must supply a project hostname")
        if not domainname:
            self._addErrors("You must supply a project domain name")
        if not self._getErrors():
            try:
                # attempt to create the project
                projectId = self.client.newProject(title, hostname,
                    domainname, projecturl, blurb)
                # now create the mailing lists
                if self.cfg.EnableMailLists and not self._getErrors():
                    if not self._createProjectLists(auth=auth,
                                                    projectName=hostname,
                                                    optlists=optlists):
                        raise mailinglists.MailingListException("Could not create the mailing lists, check the mailing list page to set up your desired lists.")
            except mailinglists.MailingListException:
                raise
            except projects.DuplicateHostname, e:
                self._addErrors(str(e))
            except projects.DuplicateName, e:
                self._addErrors(str(e))
            except mint_error.MintError, e:
                self._addErrors(str(e))
        if not self._getErrors():
            self._setInfo("Project %s successfully created" % title)
            self._redirect("http://%s%sproject/%s/" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname))
        else:
            kwargs = {'title': title, 'hostname': hostname, 'domainname': domainname, 'projecturl': projecturl, 'blurb': blurb, 'optlists': optlists}
            return self._write("newProject", kwargs=kwargs)

    @intFields(userId = None, projectId = None, level = None)
    def addMemberById(self, auth, userId, projectId, level):
        project = self.client.getProject(projectId)

        if project.getUserLevel(auth.userId) != userlevels.OWNER:
            raise mint_error.PermissionDenied

        project.addMemberById(userId, level)
        self._redirect("http://%s%sproject/%s" % (self.cfg.projectSiteHost, self.cfg.basePath, project.getHostname()))

    @requiresAuth
    @intFields(id = None)
    def userInfo(self, auth, id):
        user = self.client.getUser(id)
        userIsAdmin = self.client.isUserAdmin(id)
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
            return self._write("userInfo", user = user, userProjects = userProjects, userIsAdmin = userIsAdmin)
        else:
            raise database.ItemNotFound('userid')

    @strFields(search = "", type = None)
    @intFields(limit = 0, offset = 0, modified = 0)
    def search(self, auth, type, search, modified, limit, offset):
        limit = max(limit, 0)
        offset = max(offset, 0)
        if not limit:
            limit =  self.user and \
                    self.user.getDataValue('searchResultsPerPage') or 10
        self.session['searchType'] = type
        if type == "Projects":
            return self._projectSearch(search, modified, limit, offset)
        elif type == "Users" and self.auth.authorized:
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
            reposUrl = self.cfg.basePath + 'project/%s/' % host
            packageUrl = self.cfg.basePath + 'repos/%s/troveInfo?t=%s' % (host, quote_plus(x[0]))
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
        try:
            if not fileId:
                cmds = self.cmd.split('/')
                fileId = int(cmds[1])
                reqFilename = cmds[2]
        except ValueError:
            raise HttpNotFound

        releaseId, idx, filename, title = self.client.getFileInfo(fileId)
        if reqFilename and os.path.basename(filename) != reqFilename:
            raise HttpNotFound

        # only count downloads of the first ISO
        release = self.client.getRelease(releaseId)
        if idx == 0:
            release.incDownloads()
        try:
            project = self.client.getProject(release.projectId)

            fileUrl = "http://%s/images/%s/%d/%s" % (self.cfg.siteHost, project.hostname, release.id, reqFilename)
            self._redirect(fileUrl)
        except OSError, e:
            return self._write("error", shortError = "File error",
                error = "An error has occurred opening the image file: %s" % e)

    @requiresAuth
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def cancelAccount(self, auth, confirmed, **yesArgs):
        if confirmed:
            #do the actual deletion
            self.user.cancelUserAccount()
            self._clearAuth()
            self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self._write("confirm", message = "Are you sure you want to close your account?",
                yesArgs = {'func':'cancelAccount', 'confirmed':'1'}, noLink = self.cfg.basePath)

    def maintenance(self, auth, *args, **kwargs):
        if maintenance.getMaintenanceMode(self.cfg) == maintenance.NORMAL_MODE:
            self._redirect(self.cfg.basePath)
        elif auth.admin:
            self._redirect(self.cfg.basePath + "administer")
        else:
            return self._write("maintenance")

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
        else:
            raise HttpNotFound

        return self._writeRss(items = items, title = title, link = link, desc = desc)

    @intFields(userId = None)
    @strFields(operation = None)
    @requiresAdmin
    def processUserAction(self, auth, userId, operation):

        user = self.client.getUser(userId)
        deletedUser = False

        if operation == "user_reset_password":
            self._resetPasswordById(userId)
            self._setInfo("Password successfully reset for user %s." % \
                    user.username)
        elif operation == "user_cancel":
            if userId == self.auth.userId:
                self._addErrors("You cannot close your account from this interface.")
            else:
                self.client.removeUserAccount(userId)
                self._setInfo("Account deleted for user %s." % user.username)
                deletedUser = True

        elif operation == "user_promote_admin":
            self.client.promoteUserToAdmin(userId)
            self._setInfo("Promoted %s to administrator." % user.username)
        elif operation == "user_demote_admin":
            self.client.demoteUserFromAdmin(userId)
            self._setInfo("Revoked administrative privileges for %s." % \
                    user.username)
        else:
            self._addErrors("Please select a valid user adminstration action from the menu.")

        if deletedUser:
            return self._redirect("http://%s%s" % (self.cfg.siteHost, \
                    self.cfg.basePath))
        else:
            return self._redirect("http://%s%suserInfo?id=%d" %
                    (self.cfg.siteHost, self.cfg.basePath, userId))

    @boolFields(supported = False)
    @requiresAuth
    def rMake(self, auth, supported):
        return self._write('rMake',
                           rMakeBuilds = self.client.listrMakeBuilds(),
                           supported = supported)

    @requiresAuth
    def newrMake(self, auth):
        return self._write('newrMake')

    @strFields(title = None)
    @requiresAuth
    def createrMake(self, auth, title):
        if not re.match("[a-zA-Z0-9\-_ ]+$", title):
            self._addErrors("Invalid rMake Build name: %s" % title)
        rMakeBuild = self.client.createrMakeBuild(title)
        if self._getErrors():
            return self._write('newrMake')
        else:
            return self._redirect(self.cfg.basePath + 'editrMake?id=%d' % \
                                  rMakeBuild.id)

    @intFields(id = None)
    @requiresAuth
    def editrMake(self, auth, id):
        self.session['rMakeBuildId'] = id
        self.rMakeBuild = self.client.getrMakeBuild(id)
        # rMake Builder and Group Builder are mutually exclusive
        if 'groupTroveId' in self.session:
            del self.session['groupTroveId']
        self.session.save()
        self.groupTrove = None
        self.groupProject = None
        return self._write('editrMake')

    @strFields(title = None)
    @requiresAuth
    def editrMake2(self, auth, title):
        if not re.match("[a-zA-Z0-9\-_ ]+$", title):
            self._addErrors("Invalid rMake Build name: %s" % title)
        else:
            self.rMakeBuild.rename(title)
            self._setInfo('name successfully changed to: %s' % title)
        return self._redirect(self.cfg.basePath + 'editrMake?id=%d' % \
                                  self.rMakeBuild.id)

    @strFields(referer = '')
    @requiresAuth
    def closeCurrentrMake(self, auth, referer):
        self.rMakeBuild = None
        if 'rMakeBuildId' in self.session:
            del self.session['rMakeBuildId']
            self.session.save()
        if not referer:
            referrer = self.cfg.basePath
        self._redirect(referer)

    @dictFields(yesArgs = {})
    @boolFields(confirmed=False)
    @requiresAuth
    def deleterMakeBuild(self, auth, confirmed, **yesArgs):
        if confirmed:
            try:
                self.rMakeBuild.delete()
            except:
                self._addErrors("Unable to delete rMake Build: %s" % \
                                self.rMakeBuild.title)
            else:
                self._setInfo("Successfully deleted rMake Build: %s" % \
                              self.rMakeBuild.title)
                self.rMakeBuild = None
                if 'rMakeBuildId' in self.session:
                    del self.session['rMakeBuildId']
                    self.session.save
            return self._redirect(self.cfg.basePath)
        else:
            return self._write('confirm',
                               message = "Are you sure you want to delete " \
                               "this rMake Build: %s?" % self.rMakeBuild.title,
                               yesArgs = {'func':'deleterMakeBuild',
                                          'confirmed':'1'},
                               noLink = "rMake")

    @strFields(trvName = None, label = '', projectName = '', referer = '')
    def addrMakeTrove(self, auth, trvName, projectName, referer, label):
        if not self.rMakeBuild:
            self._addErrors("No rMake Build underway.")
        elif not label and not projectName:
            self._addErrors("No reference to trove origins given.")
        else:
            if label:
                self.rMakeBuild.addTrove(trvName, label)
            else:
                self.rMakeBuild.addTroveByProject(trvName, projectName)
            self._setInfo("Added %s" % trvName)
        if not referer:
            referer = self.cfg.basePath
        self._redirect(referer)

    @intFields(troveId = None)
    @strFields(referer = '')
    def deleterMakeTrove(self, auth, troveId, referer):
        if not self.rMakeBuild:
            self._addErrors("No rMake Build underway.")
        else:
            trvDict = self.client.getrMakeBuildTrove(troveId)
            self.client.delrMakeBuildTrove(troveId)
            self._setInfo('Successfully deleted %s' % trvDict['trvName'])
        if not referer:
            referer = self.cfg.basePath
        self._redirect(referer)

    strFields(command = None)
    def commandrMake(self, auth, command):
        if not self.rMakeBuild:
            self._addErrors("No rMake Build underway.")
            self._redirect(self.cfg.basePath)
        elif command not in ('build', 'stop', 'commit'):
            self._addErrors("Illegal rMake Command.")
            self._redirect(self.cfg.basePath)
        else:
            self._setInlineMime(self.cfg.basePath + \
                                "rMakeCommand", command = command)
            if command == 'build':
                self._setInfo("Starting rMake Build")
            elif command == 'stop':
                self._setInfo("Stopping rMake Build")
            elif command == 'commit':
                self._setInfo("Committing rMake Build")
            self._redirect(self.cfg.basePath + 'rMakeStatus')

    strFields(command = None)
    def rMakeCommand(self, auth, command):
        command = str(command)
        if not self.rMakeBuild:
            self._addErrors("No rMake Build underway.")
            self._redirect(self.cfg.basePath)
        else:
            try:
                xml = self.rMakeBuild.getXML(command)
            except Exception, e:
                self._addErrors(str(e))
                self._redirect(self.cfg.basePath)
            else:
                self.req.content_type = "application/x-rmake"
                return xml

    @requiresAuth
    def rMakeStatus(self, auth):
        if not self.rMakeBuild:
            return self._write('error', 'error', "No rMake Build underway.")
        else:
            return self._write('rMakeStatus',
                               troveList = self.rMakeBuild.listTroves())

    @requiresAuth
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def resetrMakeStatus(self, auth, confirmed, **yesArgs):
        if not self.rMakeBuild:
            return self._write('error', 'error', "No rMake Build underway.")
        if confirmed or self.rMakeBuild.status in \
               (buildjob.JOB_STATE_INIT, buildjob.JOB_STATE_FAILED,
                buildjob.JOB_STATE_COMMITTED):
            self.rMakeBuild.resetStatus()
            self._redirect(self.cfg.basePath)
        else:
            return self._write("confirm", message = "rMake Server will continue to service this rMake build but you will not be able to track it from rBuilder. Are you sure?",
                               yesArgs = {'func':'resetrMakeStatus',
                                          'confirmed':'1'},
                               noLink = self.cfg.basePath)

def helpDocument(page):
    templatePath = os.path.join(os.path.split(__file__)[0], 'templates/docs')
    return page in [x.split('.kid')[0] for x in os.listdir(templatePath) \
                    if x.endswith('.kid')]

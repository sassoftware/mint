#
# Copyright (c) 2005-2008 rPath, Inc.
#
# All rights reserved
#
import email
import os
import stat
import time
from urllib import quote, unquote, quote_plus, urlencode
from mimetypes import guess_type

from mint import buildtypes
from mint import constants
from mint import urltypes
from mint import data
from mint import helperfuncs
from mint import mint_error
from mint import maintenance
from mint import mailinglists
from mint import projects
from mint import searcher
from mint import shimclient
from mint import users
from mint import userlevels
from mint.client import timeDelta
from mint.helperfuncs import getProjectText
from mint.session import SqlSession

from mint.web.fields import boolFields, dictFields, intFields, listFields, strFields
from mint.web.decorators import mailList, requiresAdmin, requiresAuth, \
     requiresHttps, redirectHttps, redirectHttp
from mint.web.webhandler import (WebHandler, normPath, setCacheControl,
    HttpNotFound, HttpOK, HttpMethodNotAllowed, HttpForbidden)

from conary.lib import util
from conary import versions
from conary import conaryclient

from rpath_common.proddef import api1 as proddef

BUFFER=1024 * 256

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

    @redirectHttp
    def _frontPage(self, auth, *args, **kwargs):
        popularProjects = self.client.getPopularProjects()
        topProjects = self.client.getTopProjects()
        selectionData  = self.client.getFrontPageSelection()
        publishedReleases = self.client.getPublishedReleaseList()

        #insert marketing block
        frontPageBlockFile = self.cfg.frontPageBlock
        if os.path.exists(frontPageBlockFile) and os.access(frontPageBlockFile, os.R_OK):
            f = open(frontPageBlockFile, "r")
            frontPageBlock = f.read()
        else:
            frontPageBlock = ""

        return self._write("frontPage", firstTime=self.session.get('firstTimer', False),
            popularProjects=popularProjects, selectionData = selectionData,
            topProjects = topProjects,
            publishedReleases = publishedReleases,
            frontPageBlock = frontPageBlock)

    @strFields(user = '', password = '')
    def pwCheck(self, auth, user, password):
        ret = 'false'
        if not self.cfg.SSL or self.req.subprocess_env.get('HTTPS', 'off') != 'off':
            ret = str(bool(self.client.pwCheck(user, password))).lower()
        return """<auth valid="%s" />\n""" % ret

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
        if (self.cfg.rBuilderOnline or self.cfg.tosLink) and not tos:
            errors.append("You must accept the Terms of Service to create an account")
        if (self.cfg.rBuilderOnline or self.cfg.privacyPolicyLink) and not privacy:
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
            except users.InvalidUsername, e:
                errors.append(str(e))
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

    @strFields(message = "")
    @redirectHttps
    def forgotPassword(self, auth, message):
        self.toUrl = self.cfg.basePath
        return self._write("forgotPassword", message = message)

    @redirectHttp
    @strFields(page = "")
    @intFields(step = 1)
    def help(self, auth, page, step):
        if page == 'lm-project-naming':
            self._redirect("http://wiki.rpath.com/wiki/rBuilder:Create_a_Project?version=${constants.mintVersion}")
        if not helpDocument(page):
            # Redirect to the main rbuilder wiki
            self._redirect("http://wiki.rpath.com/wiki/rBuilder?version=${constants.mintVersion}")
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
            setCacheControl(self.req, strict=True)
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

                self._session_start(rememberMe)
                self.session['authToken'] = authToken
                self.session['firstTimer'] = firstTimer
                self.session['firstPage'] = unquote(to)
                user = client.getUser(auth.userId)
                if user.getDefaultedData() or (self.cfg.tosPostLoginLink and firstTimer):
                    self.session['firstPage'] = self.cfg.basePath + "userSettings"
                else:
                    client.updateAccessedTime(auth.userId)
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
        if isinstance(self.session, SqlSession):
            c = self.session.make_cookie()
            c.expires = 0
            self.req.err_headers_out.add('Set-Cookie', str(c))
            setCacheControl(self.req, strict=True)
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

    @requiresAdmin
    @intFields(sortOrder = -1, limit = 0, offset = 0)
    def users(self, auth, sortOrder, limit, offset, submit = 0):
        if not limit:
            limit =  self.user and \
                self.user.getDataValue('searchResultsPerPage') or 10

        if sortOrder < 0:
            sortOrder = self.session.get('usersSortOrder', 0)
        self.session['usersSortOrder'] = sortOrder
        results, count = self.client.getUsers(sortOrder, limit, offset)
        formattedRows, columns = self._formatUserSearch(results)
        return self._write("users", sortOrder = sortOrder, limit = limit, offset = offset,
            results = formattedRows, columns = columns, count = count)

    @requiresAuth
    @redirectHttps
    def cloudSettings(self, auth):
        return self._write("cloudSettings",
                           user = self.user,
                           dataDict = self.user.getDataDict())

    @strFields(awsAccountNumber = "", awsPublicAccessKeyId = "",
               awsSecretAccessKey = "")
    @boolFields(force = False)
    @requiresHttps
    @requiresAuth
    def processCloudSettings(self, auth, awsAccountNumber,
            awsPublicAccessKeyId, awsSecretAccessKey, force):

        def getDataDict():
            dataDict = self.user.getDataDict()
            dataDict['awsAccountNumber'] = awsAccountNumber
            dataDict['awsPublicAccessKeyId'] = awsPublicAccessKeyId
            dataDict['awsSecretAccessKey'] = awsSecretAccessKey
            return dataDict
        
        # make sure all the fields are set
        if not awsAccountNumber:
            self._addErrors("Missing account number")
        if not awsPublicAccessKeyId:
            self._addErrors("Missing access key ID")
        if not awsSecretAccessKey:
            self._addErrors("Missing secret access key")
            
        if self._getErrors():
            return self._write("cloudSettings", dataDict=getDataDict())
        
        try:
            self.client.setEC2CredentialsForUser(self.user.id,
                awsAccountNumber, awsPublicAccessKeyId, awsSecretAccessKey,
                force)
            self._setInfo("Updated EC2 settings")
            self._redirect("http://%s%suserSettings" %
                    (self.cfg.siteHost, self.cfg.basePath))
        except mint_error.MintError, e:
            self._addErrors("Failed to update EC2 settings: %s" % str(e))
            return self._write("cloudSettings", dataDict=getDataDict())
        
    @requiresAuth
    @redirectHttps
    @dictFields(yesArgs = {})
    @boolFields(confirmed = False)
    def removeCloudSettings(self, auth, confirmed, **yesArgs):
        
        if confirmed:
            # clear the credentials
            self.client.removeEC2CredentialsForUser(self.user.id)
            self._setInfo("Removed EC2 settings")
            self._redirect("http://%s%suserSettings" %
                    (self.cfg.siteHost, self.cfg.basePath))
        else:
            return self._write("confirm", 
                message = "Are you sure you want to remove your EC2 settings?",
                yesArgs = {'func':'removeCloudSettings', 'confirmed':'1'}, 
                noLink = "http://%s%suserSettings" %
                    (self.cfg.siteHost, self.cfg.basePath))

    @requiresAuth
    @redirectHttps
    def userSettings(self, auth):
        return self._write("userSettings",
                           user = self.user,
                           dataDict = self.user.getDataDict(),
                           defaultedData = self.user.getDefaultedData(),
                           firstTimer=self.session.get('firstTimer', True))

    @strFields(email = "", displayEmail = "",
               password1 = "", password2 = "",
               fullName = "", blurb = "", tos = "")
    @requiresHttps
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, fullName,
                         password1, password2, blurb, tos, **kwargs):
        
        if self.session.get('firstTimer', True):
            # first time logging in
            if self.cfg.tosPostLoginLink and not tos:
                return self._write("error", shortError = "Registration Error",
                    error = "You must accept the Terms of Service to continue.")
            self.client.updateAccessedTime(auth.userId)
        
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

        for key, (dType, default, prompt, errordesc, helpText, password) in \
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
        projectList = sorted((
                (x[0].getName(), x[0].getHostname())
                for x in self.projectList
                if not x[0].external and x[1] in userlevels.WRITERS
            ), key=lambda y: y[0])
        if self.projectList:
            return self._write("uploadKey", kwargs={}, projects=projectList)
        else:
            pText = getProjectText().lower()
            return self._write("error", shortError="Not a %s member"%pText,
                error = "You may not upload a key as you are not a member of any %ss. "
                        "Create a %s, or ask a %s owner to add you to their "
                        "%s and then come back"%(pText,pText,pText,pText))

    @requiresAuth
    @listFields(str, projects=None)
    @strFields(keydata=None)
    def processKey(self, auth, projects, keydata):
        pText = getProjectText().lower()
        projectList = sorted((
                (x[0].getName(), x[0].getHostname())
                for x in self.projectList
                if not x[0].external and x[1] in userlevels.WRITERS
            ), key=lambda y: y[0])

        added = []
        for project, level, memberReqs in self.projectList:
            if project.getHostname() in projects and level in userlevels.WRITERS:
                try:
                    project.addUserKey(auth.username, keydata)
                except Exception, e:
                    self._addErrors('Error uploading key: %s' % str(e))
                    return self._write("uploadKey",
                            kwargs={'projects': projects, 'keydata': keydata},
                            projects=projectList)
                else:
                    added.append(project)

        c = len(added)
        self._setInfo("Added key to %d %s" % (c, (c == 1) and pText or "%ss"%pText))
        self._redirect("http://%s%s" % (self.cfg.siteHost, self.cfg.basePath))

    @requiresAuth
    def newProject(self, auth):
        availablePlatforms = self.client.getAvailablePlatforms()
        try:
            platformLabel = availablePlatforms[0][0]
        except IndexError:
            platformLabel = ''

        return self._write("newProject", errors=[], 
           availablePlatforms = availablePlatforms,
           customPlatform = None,
           kwargs={'domainname': self.cfg.projectDomainName.split(':')[0], 
                   'appliance': 'unknown', 
                   'prodtype' : 'Appliance', 
                   'namespace': self.cfg.namespace,
                   'isPrivate': False,
                   'platformLabel': platformLabel})

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

    @strFields(title = '', hostname = '', domainname = '', projecturl = '', 
               blurb = '', appliance = 'unknown', shortname = '', namespace='',
               prodtype = '', version = '', commitEmail='', isPrivate = 'off',
               platformLabel = '')
    @listFields(int, optlists = [])
    @requiresAuth
    def createProject(self, auth, title, hostname, domainname, projecturl, 
                      blurb, optlists, appliance, shortname, namespace, 
                      prodtype, version, commitEmail, isPrivate, platformLabel):
        isPrivate = (isPrivate.lower() == 'on') and True or False
        
        shortname = shortname.lower()
        if not hostname:
            hostname = shortname

        pText = getProjectText().lower()
        if not namespace:
            self._addErrors('You must supply a %s namespace' % pText)
        if not title:
            self._addErrors("You must supply a %s title"%pText)
        if not shortname:
            self._addErrors("You must supply a %s short name"%pText)
        if not prodtype or prodtype == 'unknown':
            self._addErrors("You must select a %s type"%pText)
        if not version or len(version) <= 0:
            self._addErrors("You must supply a %s version"%pText)

        # For rBO, use the default domain name unconditionally
        if self.cfg.rBuilderOnline:
            domainname = self.cfg.projectDomainName.split(':')[0]

        if not self._getErrors():
            try:
                # attempt to create the project
                projectId = self.client.newProject(title, hostname,
                    domainname, projecturl, blurb, appliance, shortname, 
                    namespace, prodtype, version, commitEmail, isPrivate,
                    platformLabel)
                
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
            # attempt to create the project version
            try:
                versionId = self.client.addProductVersion(projectId, namespace, version);
                pd = proddef.ProductDefinition()
                pd = helperfuncs.sanitizeProductDefinition(title,
                        blurb, hostname, domainname, shortname, version,
                        '', namespace)
                self.client.setProductDefinitionForVersion(versionId, pd, platformLabel)

            except projects.DuplicateProductVersion, e: 
                self._addErrors(str(e))
            except projects.ProductVersionInvalid, e:
                    self._addErrors(str(e))
                
        if not self._getErrors():
            # don't output status here since we now move on the updating the 
            # version.  Status will be updated after that.
            self._redirect("http://%s%sproject/%s/editVersion?id=%d&linked=%s" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname, versionId, title))
        else:
            availablePlatforms = self.client.getAvailablePlatforms()
            kwargs = {'title': title, 
                      'hostname': hostname, 
                      'domainname': domainname, 
                      'projecturl': projecturl, 
                      'blurb': blurb, 
                      'optlists': optlists, 
                      'appliance': appliance,
                      'commitEmail': commitEmail,
                      'shortname' : shortname, 
                      'prodtype' : prodtype, 
                      'namespace' : namespace,
                      'version' : version,
                      'isPrivate' : isPrivate,
                      'platformLabel': platformLabel}
            return self._write("newProject", availablePlatforms=availablePlatforms,
                    kwargs=kwargs)

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
            raise mint_error.ItemNotFound('userid')

    @strFields(search = "", type = None)
    @intFields(limit = 0, offset = 0, modified = 0, removed = 0, showAll = 0, byPopularity = 0)
    def search(self, auth, type, search, modified, limit, offset, removed, showAll, byPopularity):
        limit = max(limit, 0)
        offset = max(offset, 0)
        if not limit:
            limit =  self.user and \
                    self.user.getDataValue('searchResultsPerPage') or 10
        self.session['searchType'] = type
        if type in ("Products", "Projects"):
            return self._projectSearch(search, modified, limit, offset, removed, not showAll)
        elif type == "Users" and self.auth.authorized:
            return self._userSearch(auth, search, limit, offset)
        elif type == "Packages":
            if self.groupTrove and not removed:
                for x in self.groupTrove.listTroves():
                    if x['trvName'] == 'group-appliance-platform':
                        label = versions.Label(x['trvLabel'])
                        labelLimiter = "branch=%s:%s" % \
                                (label.getNamespace(), label.getLabel())
                        if labelLimiter not in search:
                            search += " %s" % labelLimiter
                        self._setInfo("Because you are building a group, only search results compatible with your group are shown.")
                        break

            return self._packageSearch(search, limit, offset, removed)
        else:
            self.session['searchType'] = ''
            return self._write("error", shortError = "Invalid Search Type",
                error = "Invalid search type specified.")

    #
    # User search
    #

    def _formatUserSearch(self, results):
        if self.auth.admin:
            columns = ('User Name', 'Full Name', 'Account Created', 'Last Accessed', 'Status')
        else:
            columns = ('User Name', 'Full Name', 'Account Created', 'Last Accessed')

        formattedRows = []
        for result in results:
            link = self.cfg.basePath + 'userInfo?id=%d' % result[0]
            row = {
                'columns': [(link, result[1]), result[2], timeDelta(result[5]), timeDelta(result[6])],
            }

            if self.auth.admin:
                row['columns'].append(result[7] and "Active" or "Inactive")
            formattedRows.append(row)
        return formattedRows, columns

    def _userSearch(self, auth, terms, limit, offset):
        results, count = self.client.getUserSearchResults(terms, limit, offset)

        formattedRows, columns = self._formatUserSearch(results)
        self.searchTerms = terms
        return self._write("searchResults", searchType = "Users", 
            terms = terms, fullTerms = terms, results = formattedRows,
            columns = columns, count = count, limit = limit,
            offset = offset, modified = 0, limiters = [],
            limitsRemoved = False, extraParams = "")

    #
    # Package search
    #

    def _formatPackageSearch(self, results):
        pText = getProjectText().title()
        if self.groupTrove:
            columns = ('Package', pText, '')
        else:
            columns = ('Package', pText)

        formattedRows = []
        for troveName, troveVersionStr, projectId in results:
            p = self.client.getProject(projectId)
            projectHost = p.getHostname()
            projectName = p.name
            reposUrl = self.cfg.basePath + 'project/%s/' % projectHost
            packageUrl = self.cfg.basePath + 'repos/%s/troveInfo?t=%s;v=%s' % (projectHost, quote_plus(troveName), quote_plus(troveVersionStr))

            ver = versions.VersionFromString(troveVersionStr)

            row = {
                'columns':  [(packageUrl, troveName), (reposUrl, projectName)],
                'desc':     '%s=%s/%s' % (troveName, ver.trailingLabel(), ver.trailingRevision()),
            }

            # show the group trove links?
            if self.groupTrove:
                name = 'Add to %s' % self.groupTrove.recipeName
                link = self.cfg.basePath + 'project/%s/addGroupTrove?id=%d;trove=%s;version=%s;referer=%s' % \
                    (self.groupTrove.projectName, self.groupTrove.getId(), quote(troveName), troveVersionStr, quote(self.req.unparsed_uri))
                row['columns'].append((link, name))

            formattedRows.append(row)
        return formattedRows, columns

    def _packageSearch(self, terms, limit, offset, limitsRemoved = False):
        results, count = self.client.getPackageSearchResults(terms, limit, offset)

        def describeFn(key, val):
            termNames = {
                'branch': "only packages for %s branch",
                'server': "only packages on %s server",
            }
            return termNames[key] % val

        fullTerms = terms
        limiters, terms = searcher.limitersForDisplay(fullTerms, describeFn)

        formattedRows, columns = self._formatPackageSearch(results)

        terms = " ".join(terms)
        self.searchTerms = terms
        return self._write("searchResults", searchType = "Packages",
            terms = terms, fullTerms = fullTerms, results = formattedRows,
            columns = columns, count = count, limit = limit, offset = offset,
            modified = 0, limiters = limiters,
            limitsRemoved = limitsRemoved, extraParams = "")

    #
    # Project search
    # 
    def _formatProjectSearch(self, results):
        pText = getProjectText().title()
        columns = (pText, 'Last Commit', 'Last Release')
        formattedRows = []
        for x in results:
            p = self.client.getProject(x[0])

            row = {
                'columns': [(p.getUrl(), p.getNameForDisplay()), timeDelta(x[4]), x[6] and timeDelta(x[6]) or "None"],
                'desc':    p.getDescForDisplay(),
            }

            formattedRows.append(row)
        return formattedRows, columns

    def _projectSearch(self, terms, modified, limit, offset, limitsRemoved = False, filterNoDownloads = True):
        pText = getProjectText()
        results, count = self.client.getProjectSearchResults(terms, modified, limit, offset,
            filterNoDownloads = filterNoDownloads)

        buildTypes = list(set(self.client.getAvailableBuildTypes() + [buildtypes.XEN_DOMU]) - \
                set([ int(v) for k, v in searcher.parseLimiters(terms) \
                    if k == 'buildtype' ]))

        def describeFn(key, val):
            if key == "buildtype":
                return "%s containing %s builds" % (pText.lower(),buildtypes.typeNamesMarketing[int(val)])
            else:
                return ""

        formattedRows, columns = self._formatProjectSearch(results)

        fullTerms = terms
        limiters, terms = searcher.limitersForDisplay(fullTerms, describeFn)

        terms = " ".join(terms)

        if terms.strip() != "" or limiters:
            filterNoDownloads = False
        self.searchTerms = terms
        
        if filterNoDownloads:
            extraParams = ""
        else:
            extraParams = ";showAll=1"
        
        return self._write("searchResults", searchType = pText.title()+'s',
                terms = terms, fullTerms = fullTerms,
                results = formattedRows,
                columns = columns, count = count, limit = limit,
                offset = offset, modified = modified, limiters = limiters,
                limitsRemoved = limitsRemoved,
                filterNoDownloads = filterNoDownloads,
                buildTypes = buildTypes,
                extraParams = extraParams)

    @intFields(fileId = 0, urlType = urltypes.LOCAL)
    def downloadImage(self, auth, fileId, urlType):
        reqFilename = None
        try:
            if not fileId:
                cmds = self.cmd.split('/')
                fileId = int(cmds[1])
                reqFilename = cmds[2]
        except ValueError:
            raise HttpNotFound

        # Screen out UrlTypes that are not visible, except for urltypes.LOCAL,
        # which is ALWAYS visible.
        if not (urlType == urltypes.LOCAL \
                or urlType in self.cfg.visibleUrlTypes):
            raise HttpNotFound

        try:
            buildId, idx, title, fileUrls = self.client.getFileInfo(fileId)
        except mint_error.FileMissing:
            raise HttpNotFound

        # Special rules for handling the default case (urltypes.LOCAL):
        # If self.cfg.redirectUrlType is set AND that FileUrl exists,
        # then use it.
        redirectUrl = None
        overrideRedirect = None
        filename = None

        urlIdMap = {}
        for urlId, t, u in fileUrls:
            urlIdMap[u] = urlId
            if t == urltypes.LOCAL:
                filename = u
            elif t == urlType:
                redirectUrl = u

            if t == self.cfg.redirectUrlType:
                overrideRedirect = u

        # For urltype.LOCAL, construct the redirect URL
        # Use override redirect if it's set (e.g. redirecting to Amazon S3).

        serveOurselves = False
        if urlType == urltypes.LOCAL:
            if overrideRedirect:
                redirectUrl = overrideRedirect
            elif filename:
                # Don't pass through bad filenames if they are specified in
                # the request.
                if reqFilename and os.path.basename(filename) != reqFilename:
                    raise HttpNotFound

                if not os.path.exists(filename):
                    raise HttpNotFound

                size = os.stat(filename)[stat.ST_SIZE]
                if size >= (1024*1024) * 2047:
                    serveOurselves = True

                build = self.client.getBuild(buildId)
                project = self.client.getProject(build.projectId) 
                redirectUrl = "http://%s/images/%s/%d/%s" % (self.cfg.siteHost, project.hostname, build.id, os.path.basename(filename))

        # record the hit
        urlId = urlIdMap.get(redirectUrl, urlIdMap.get(filename, None))
        if urlId:
            self.client.addDownloadHit(urlId, self.remoteIp)

        # apache 2.0 has trouble sending >2G files
        if serveOurselves:
            self.req.headers_out['Content-length'] = str(size)
            self.req.headers_out['Content-Disposition'] = \
                "attachment; filename=%s;" % os.path.basename(filename)
            typeGuess = guess_type(filename)
            if typeGuess[0]:
                self.req.content_type = typeGuess[0]
            else:
                self.req.content_type = "application/octet-stream"
            imgF = file(filename)
            util.copyfileobj(imgF, self.req)
            return HttpOK
        if redirectUrl:
            self._redirect(redirectUrl)
        else:
            raise HttpNotFound


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
        pText = getProjectText()
        if feed == "newProjects":
            results = self.client.getNewProjects(10, showFledgling = False)

            title = "%s - New %ss" % (self.cfg.productName,pText.title())
            link = "http://%s%srss?feed=newProjects" % (self.cfg.siteHost, self.cfg.basePath)
            desc = "New %ss created on %s" % (pText.lower(),self.cfg.productName) 

            items = []
            for p in results:
                item = {}
                project = self.client.getProject(p[0])

                item['title'] = project.getName()
                item['link'] = project.getUrl()
                item['content'] = "<p>A new %s named <a href=\"%s\">%s</a> has been created.</p>" % \
                    (pText.lower(),project.getUrl(), project.getName())
                desc = project.getDesc().strip()
                if desc:
                    item['content'] += "%s description:"%pText.title()
                    item['content'] += "<blockquote>%s</blockquote>" % desc
                item['date_822'] = email.Utils.formatdate(project.getTimeCreated())
                item['creator'] = "http://%s%s" % (self.siteHost, self.cfg.basePath)
                items.append(item)
        elif feed == "newReleases":
            results = self.client.getPublishedReleaseList()
            title = "%s - Latest releases" % self.cfg.productName
            link = "http://%s%srss?feed=newReleases" % (self.cfg.siteHost, self.cfg.basePath)
            desc = "New releases published on %s" % self.cfg.productName

            items = []
            for p in results:
                item = {}
                projectName, hostname, release = p
                item['title'] = "%s" % release.name
                if release.version:
                    item['title'] += " (version %s)" % (release.version)
                item['link'] = 'http://%s%sproject/%s/release?id=%d' % (self.cfg.projectSiteHost, self.cfg.basePath, hostname, release.getId())
                item['content'] = "<p>A new release has been published by the <a href=\"http://%s%sproject/%s\">%s</a> %s.</p>\n" % (self.cfg.projectSiteHost, self.cfg.basePath, hostname, projectName, pText.lower())
                item['content']  += "This release contains the following builds:"
                item['content'] += "<ul>"
                builds = [self.client.getBuild(x) for x in release.getBuilds()]
                for build in builds:
                    item['content'] += "<li><a href=\"http://%s%sproject/%s/build?id=%ld\">%s (%s %s)</a></li>" % (self.cfg.siteHost, self.cfg.basePath, hostname, build.id, build.getName(), build.getArch(), buildtypes.typeNamesShort[build.buildType])
                item['content'] += "</ul>"

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

    @requiresAuth
    @strFields(trvName = None, trvVersion = None)
    def findRefs(self, auth, trvName, trvVersion):
        # this call is flavor-agnostic, but we have to find all
        # the flavors of the requested trove so we can use that
        # list to call getTroveReferences.
        references = self.client.getTroveReferences(trvName, trvVersion)

        # getTroveDescendants can be flavor-agnostic.
        branch = versions.VersionFromString(trvVersion).branch()
        descendants = self.client.getTroveDescendants(trvName, str(branch), '')

        references = dict((self.client.getProject(x[0]), set((y[0], y[1]) for y in x[1])) for x in references.items() if x[1])
        descendants = dict((self.client.getProject(x[0]), set((trvName, y[0], y[1]) for y in x[1])) for x in descendants.items() if x[1])

        return self._write("findRefs",
            trvName = trvName, trvVersion = trvVersion,
            references = references, descendants = descendants)

    @intFields(id = -1)
    def tryItNow(self, auth, id):
        try:
            bami = self.client.getBlessedAMI(id)
        except mint_error.ItemNotFound:
            raise HttpNotFound

        if not bami.isAvailable:
            raise HttpNotFound

        return self._write("tryItNow",
                blessedAMIId = bami.id,
                ec2AMIId = bami.ec2AMIId,
                buildId = bami.buildId,
                shortDescription = bami.shortDescription,
                helptext = bami.helptext)

    def uploadBuild(self, auth):
        method = self.req.method.upper()
        if method != "PUT":
            raise HttpMethodNotAllowed

        client = shimclient.ShimMintClient(self.cfg, (self.cfg.authUser,
                                                      self.cfg.authPass))

        buildId, fileName = self.req.uri.split("/")[-2:]
        build = client.getBuild(int(buildId))
        project = client.getProject(build.projectId)

        # make sure the hash we receive from the slave matches
        # the hash we gave the slave in the first place.
        # this prevents slaves from overwriting arbitrary files
        # in the finished images directory.
        outputToken = self.req.headers_in.get('X-rBuilder-OutputToken')
        if outputToken != build.getDataValue('outputToken', validate = False):
            raise HttpForbidden

        targetFn = os.path.join(self.cfg.imagesPath, project.hostname, str(buildId), fileName)
        util.mkdirChain(os.path.dirname(targetFn))

        targetF = open(targetFn, 'w+')
        util.copyfileobj(self.req, targetF)
        return ''

    def cloudCatalog(self, auth):
        userCredentials = self.client.getEC2CredentialsForUser(self.auth.userId)
        template = userCredentials.get('awsAccountNumber', None) and \
                'cloudCatalog' or 'cloudCatalogNoCredentials'
        return self._write(template)


def helpDocument(page):
    templatePath = os.path.join(os.path.split(__file__)[0], 'templates/docs')
    return page in [x.split('.kid')[0] for x in os.listdir(templatePath) \
                    if x.endswith('.kid')]

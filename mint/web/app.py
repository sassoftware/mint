#
# Copyright (c) 2005 rpath, Inc.
#
# All rights reserved
#
import base64
import os
import kid
import stat
import sys
import time
from urllib import quote, unquote

from mod_python import apache
from mod_python import Cookie

import repository
import versions
from deps import deps
from web import webhandler
from web import fields
from web.fields import strFields, intFields, listFields, boolFields

from mint import database
from mint import jobs
from mint import mint_error
from mint import mint_server
from mint import projects
from mint import releases
from mint import releasetypes
from mint import shimclient
from mint import users
from mint import userlevels
from mint import mailinglists

class Redirect(Exception):
    def __init__(self, location):
        self.location = location

    def __str__(self):
        return "Location: %s" % self.location

def requiresAuth(func):
    def wrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise mint_error.PermissionDenied
        else:
            return func(self, **kwargs)
    return wrapper

def siteOnly(func):
    """
    Decorator to ensure that a webapp method accessed using a 
    <project>.rpath.org url is redirected to the site url; eg:
    www.rpath.org.
    """
    def wrapper(self, **kwargs):
        if self.project:
            if self.cfg.hostName:
                host = "%s.%s" % (self.cfg.hostName, self.cfg.domainName)
            else:
                host = self.cfg.domainName
            newLoc = ("http://%s" % host) + self.req.unparsed_uri
            return self._redirect(newLoc)
        else:
            return func(self, **kwargs)
    return wrapper

def projectOnly(func):
    """
    Decorator to return a 404 Not Found error if a webapp method
    that requires a project is accessed at the site url.
    """
    def wrapper(self, **kwargs):
        if not self.project:
            return self._404(self, **kwargs)
        else:
            return func(self, **kwargs)
    return wrapper

def ownerOnly(func):
    """
    Decorate a method to be callable only by the owner of the
    current package also requires that a package exist.
    """
    def wrapper(self, **kwargs):
        if not self.project:
            raise database.ItemNotFound("project")
        if self.userLevel == userlevels.OWNER:
            return func(self, **kwargs)
        else:
            raise mint_error.PermissionDenied
    return wrapper

def mailList(func):
    """
    Decorate a method so that it is passed a MailingListClient object
    properly formatted and ready to use inside an error handler.
    """
    def wrapper(self, **kwargs):
        mlists = mailinglists.MailingListClient(self.cfg.MailListBaseURL + 'xmlrpc')
        try:
            return func(self, mlists=mlists, **kwargs)
        except mailinglists.MailingListException, e:
            self._write("error", shortError = "Mailing List Error",
                    error = "An error occured while talking to the mailing list server: %s" % str(e))
            return apache.OK
    return wrapper

class MintApp(webhandler.WebHandler):
    """
    The Mint web application handler.
    @cvar auth: a L{mint.users.Authorization} object for the user who is currently logged in.
    @type auth: L{mint.users.Authorization}
    @cvar cfg: the server's L{mint.config.MintConfig} object
    @type cfg: L{mint.config.MintConfig}
    @cvar client: a L{mint.mint.MintClient} object
    @type client: L{mint.mint.MintClient}
    @cvar cmd: the current web command extracted from the request path.
    @type cmd: str
    @cvar cookies: dictionary of cookies (should not be an object member; will go away)
    @type cookies: mod_python.Cookie
    @cvar req: mod_python request object (should probably not be an object member)
    @type req: mod_python.request_rec
    @cvar project: a L{mint.projects.Project} object for the currently selected project; None if no project is selected.
    @type project: L{mint.projects.Project}
    @cvar user: a L{mint.users.User} object of user who is currently logged in.
    @type user: L{mint.users.User}
    @cvar userLevel: one of L{mint.userlevels.LEVELS} for the project and user currently logged in.
    @type userLevel: int
    @cvar projectList: list of logged-in user's projects.
    @type projectList: list of L{mint.projects.Project}
    """ 
    __slots__ = ('auth', 'cfg', 'client', 'cmd', 'cookies',
                 'project', 'req', 'user', 'userLevel')

    auth = None
    cfg = None
    client = None
    cmd = None
    cookies = None
    req = None
    project = None
    user = None
    userLevel = None
    projectList = None
    
    content_type = "application/xhtml+xml"

    def _checkAuth(self, authToken):
        self.client = shimclient.ShimMintClient(self.cfg, authToken)
        auth = self.client.checkAuth()
        return auth

    def _404(self, *args, **kwargs):
        return apache.HTTP_NOT_FOUND

    def _getHandler(self, cmd, auth):
        fullHost = self.req.hostname
        self.toUrl = ("http://%s" % fullHost) + self.req.unparsed_uri
        dots = fullHost.split('.')
        hostname = dots[0]

        # slightly hairy logic:
        # if the hostname is the site hostname (eg: mint.rpath.org),
        # great. if it's in reserved hosts, redirect to site hostname.
        # if neither, check to see if it's a valid project. if so,
        # show the project page. if not, redirect to site hostname.
        if self.cfg.hostName:
            siteHost = "%s.%s" % (self.cfg.hostName, self.cfg.domainName)
        else:
            siteHost = self.cfg.domainName
        self.siteHost = siteHost
        
        self.userLevel = -1
        if len(dots) == 3:
            if hostname == self.cfg.hostName:
                default = self._frontPage
            elif hostname in mint_server.reservedHosts and\
                ".".join(dots[1:]) == self.cfg.domainName:
                raise Redirect(("http://%s" % siteHost) + self.req.unparsed_uri)
            else:
                try:
                    self.project = self.client.getProjectByFQDN(fullHost)
                    self.userLevel = self.project.getUserLevel(self.auth.userId)
                except database.ItemNotFound:
                    # XXX just for the testing period
                    raise Redirect("http://rpath.com/")
                    # raise Redirect(("http://%s" % siteHost) + self.req.unparsed_uri)
                else:
                    default = self.projectPage
        elif fullHost == self.cfg.domainName:
            # if hostName is set, require it for access:
            if self.cfg.hostName:
                raise Redirect("http://rpath.com/")
            else:
                self.userLevel = -1
                default = self._frontPage
           
        try:
            if not cmd:
               method = default
            else:
               method = self.__getattribute__(cmd)
        except AttributeError:
            return self._404

        if auth.stagnant and cmd not in ['editUserSettings','confirm','logout']:
            return self.confirmEmail
        if not callable(method):
            method = self._404
        return method

    def _methodHandler(self):
        if 'authToken' in self.cookies:
            auth = base64.decodestring(self.cookies['authToken'].value)
            authToken = auth.split(":")

            auth = self._checkAuth(authToken)

            if not auth.authorized:
                self._clearAuth()
                return self._redirect("/")
            else:
                self.user = self.client.getUser(auth.userId)
                self.projectList = self.client.getProjectsByMember(auth.userId)
        else:
            authToken = ('anonymous', 'anonymous')
            self._checkAuth(authToken)
            auth = users.Authorization()

        self.authToken = authToken
        self.auth = auth
        auth.setToken(authToken)

        if self.cmd.startswith("_"):
            return apache.HTTP_NOT_FOUND

        try:
            method = self._getHandler(self.cmd, auth)
        except Redirect, e:
            return self._redirect(e.location)
            
        d = dict(self.fields)
        d['auth'] = self.auth
        try:
            return method(**d)
        except mint_error.MintError, e:
            err_name = sys.exc_info()[0].__name__
            self.req.log_error("%s: %s" % (err_name, str(e)))
            self._write("error", shortError = err_name, error = str(e))
            return apache.OK
        except fields.MissingParameterError, e:
            self._write("error", shortError = "Missing Parameter", error = str(e))
            return apache.OK

    def _redirCookie(self, cookie):
        # we have to add the cookie headers manually when redirecting, because
        # mod_python looks at err_headers_out instead of headers_out.

        self.req.err_headers_out.add("Cache-Control", 'no-cache="set-cookie"')
        self.req.err_headers_out.add("Set-Cookie", str(cookie))

    def _clearAuth(self):
        for domain in self.cfg.cookieDomain:
            cookie = Cookie.Cookie('authToken', '', domain = "." + domain,
                                                    expires = time.time() - 300,
                                                    path = "/")
            self._redirCookie(cookie)

    def _conaryConfig(self, project):
        cfg = project.getConaryConfig()

        cfg.setValue("dbPath", ":memory:")
        cfg.setValue("root", ":memory:")
        return cfg                    

    @siteOnly
    def _frontPage(self, auth):
        news = self.client.getNews()
        self._write("frontPage", news = news, newsLink = self.client.getNewsLink())
        return apache.OK

    @siteOnly
    def register(self, auth):
        self._write("register", errors=[], kwargs={})
        return apache.OK

    @siteOnly
    @strFields(username = '', email = '', password = '', password2 = '', fullName = '', displayEmail = '', blurb = '', tos='', privacy='')
    def processRegister(self, auth, username, fullName, email, password, password2, displayEmail, blurb, tos, privacy):
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
            kwargs = {'username': username, 'email': email, 'fullName': fullName, 'displayEmail': displayEmail, 'blurb': blurb, 'tos': tos, 'privacy': privacy}
            self._write("register", errors=errors, kwargs = kwargs)
        return apache.OK

    @siteOnly
    def confirmEmail(self, auth, **kwargs):
        self._write("confirmEmail", email=auth.email)
        return apache.OK

    @siteOnly
    @strFields(page = None)
    def legal(self, auth, page):
        if page not in ["tos", "privacy"]:
            return apache.NOT_FOUND
            
        self._write(page)
        return apache.OK

    @siteOnly
    @strFields(message = "")
    def login(self, auth, message):
        self.toUrl = "/"
        self._write("login", message = message)
        return apache.OK

    @siteOnly
    def logout(self, auth):
        self._clearAuth()
        return self._redirect("/")

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
                auth = base64.encodestring("%s:%s" % authToken).strip()
                for domain in self.cfg.cookieDomain:
                    cookie = Cookie.Cookie('authToken', auth, domain = "." + domain, path = "/")
                    self._redirCookie(cookie)
                return self._redirect(unquote(to))
        elif submit == "Forgot Password":
            newpw = users.newPassword()
            
            userId = self.client.getUserIdByName(username)
            user = self.client.getUser(userId)
            user.setPassword(newpw)

            message = "\n".join(["Your password for username %s at rpath.com has been reset to:" % user.getUsername(),
                                 "",
                                 "    %s" % newpw,
                                 "",
                                 "Please log in at http://www.rpath.com/ and change",
                                 "this password as soon as possible."])

            users.sendMail(self.cfg.adminMail, "rpath.com", user.getEmail(),
                           "rpath.com forgotten password", message)
            self._write("forgotPassword", email = user.getEmail())
            return apache.OK
        else:
            return apache.HTTP_NOT_FOUND

    @siteOnly
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

    # XXX disabled
    # @intFields(sortOrder = 0, limit = 10, offset = 0)
    # def users(self, auth, sortOrder, limit, offset, submit = 0):
    #     results, count = self.client.getUsers(sortOrder, limit, offset)
    #     self._write("users", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)
    #     return apache.OK

    @projectOnly
    def projectPage(self, auth):
        self._write("projectPage")
        return apache.OK

    @projectOnly
    def releases(self, auth):
        releases = self.project.getReleases(showUnpublished = True)
        
        #releasesByTrove = {}
        #for release in releases:
        #    l = releasesByTrove.setdefault(release.getTroveName(), [])
        #    l.append(release)
        #for l in releasesByTrove.values():
        #    l.sort(key = lambda x: x.getTroveVersion(), reverse = True)

        self._write("releases", releases = releases)
        return apache.OK

    @projectOnly
    @ownerOnly
    def newRelease(self, auth):
        self._write("newRelease")
        return apache.OK

    @projectOnly
    @ownerOnly
    @intFields(releaseId = -1, imageType = releasetypes.INSTALLABLE_ISO)
    @strFields(trove = "", releaseName = "")
    def editRelease(self, auth, releaseId, imageType, trove, releaseName):
        projectId = self.project.getId()
        if releaseId == -1:
            assert(projectId != -1)
            release = self.client.newRelease(projectId, releaseName)

            release.setImageType(imageType)
            trove, label = trove.split("=")
            label = versions.Label(label)
            version = None
            flavor = None
        else:
            release = self.client.getRelease(releaseId)

            trove, versionStr, flavor = release.getTrove()
            version = versions.ThawVersion(versionStr)
            label = version.branch().label()

        cfg = self._conaryConfig(self.project)
        netclient = repository.netclient.NetworkRepositoryClient(cfg.repositoryMap)
        leaves = netclient.getTroveLeavesByLabel({trove: {label: None}})
   
        # group troves by major architecture
        def dictByArch(leaves, troveName):
            archMap = {}
            for v, flavors in reversed(sorted(leaves[troveName].items())):
                for f in flavors:
                    arch = f.members[deps.DEP_CLASS_IS].members.keys()[0]

                    l = archMap.setdefault(arch, [])
                    l.append((v, f, ))
            return archMap

        archMap = dictByArch(leaves, trove)
        versionFlavors = []
        for arch, vfList in archMap.items():
            for vf in vfList:
                versionFlavors.append(vf)
        versionFlavors.sort(key=lambda x: x[0], reverse=True)

        self._write("editRelease", trove = trove, version = version,
                                   flavor = deps.ThawDependencySet(flavor),
                                   label = label.asString(), release = release,
                                   archMap = archMap)
        return apache.OK

    @requiresAuth
    @projectOnly
    @intFields(releaseId = None)
    @strFields(trove = None, version = None,
               desc = "", mediaSize = "640")
    def editRelease2(self, auth, releaseId,
                     trove, version,
                     desc, mediaSize):
        release = self.client.getRelease(releaseId)

        version, flavor = version.split(" ")
        release.setTrove(trove, version, flavor)
        release.setDesc(desc)

        flavor = deps.ThawDependencySet(flavor)
        jobArch = flavor.members[deps.DEP_CLASS_IS].members.keys()[0]
        assert(jobArch in ('x86', 'x86_64'))

        try:
            job = self.client.startImageJob(releaseId)
        except jobs.DuplicateJob:
            pass

        return self._redirect("release?id=%d" % releaseId)

    @projectOnly
    @intFields(id = None)
    def release(self, auth, id):
        release = self.client.getRelease(id)

        try:
            trove, version, flavor = release.getTrove()
        except releases.TroveNotSet:
            return self._redirect("editRelease?releaseId=%d" % release.getId())
        else:
            self._write("release", release = release,
                                   name = release.getName(),
                                   trove = trove, version = versions.ThawVersion(version),
                                   flavor = deps.ThawDependencySet(flavor),
                                   releaseId = id, projectId = self.project.getId())
        return apache.OK

    @projectOnly
    @ownerOnly
    @intFields(releaseId = None)
    def publish(self, auth, releaseId):
        release = self.client.getRelease(releaseId)
        release.setPublished(True)

        return self._redirect("release?id=%d" % releaseId)

    @projectOnly
    @ownerOnly
    @intFields(releaseId = None)
    def restartJob(self, auth, releaseId):
        self.client.startImageJob(releaseId)
        return self._redirect("release?id=%d" % releaseId)

    @projectOnly
    @mailList
    def mailingLists(self, auth, mlists):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        hostname = self.project.getHostname()
        lists = mlists.list_lists(hostname)
        self._write("mailingLists", lists=lists, mailhost=self.cfg.MailListBaseURL, hostname=hostname)
        return apache.OK

    @projectOnly
    @ownerOnly
    @strFields(listname=None, description='', listpw='', listpw2='')
    @mailList
    def createList(self, auth, mlists, listname, description, listpw, listpw2):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        if listpw == listpw2:
            members = self.project.getMembers()
            owners = []
            for member in members:
                if member[2] == userlevels.OWNER:
                    owner = self.client.getUser(member[0])
                    owners.append(owner.getEmail())
            hostname = self.project.getHostname()
            if not mlists.add_list(self.cfg.MailListPass, hostname+'-'+listname, listpw, description, owners):
                raise mailinglists.MailingListException("Mailing list not created")
            return self._redirect("mailingLists")
        else:
            raise mailinglists.MailingListException("Passwords do not match")

    @projectOnly
    @ownerOnly
    @strFields(list=None)
    @mailList
    def _deleteList(self, auth, mlists, list):
        hostname = self.project.getHostname()
        pcre = re.compile('^%s$|^%s-'%(hostname, hostname), re.I)
        if pcre.search(list):
            if not mlists.delete_list(self.cfg.MailListPass, list, True):
                raise mailinglists.MailingListException("Mailing list not deleted")
        else:
            raise mailinglists.MailingListException("You cannot delete this list")
        return self._redirect("mailingLists") 

    @requiresAuth
    @projectOnly
    @strFields(list=None)
    @mailList
    def subscribe(self, auth, mlists, list):
        if not self.cfg.EnableMailLists:
            raise mailinglists.MailingListException("Mail Lists Disabled")
        mlists.server.subscribe(list, self.cfg.MailListPass, [auth.email], False, True)
        return self._redirect("mailingLists")
        
    @siteOnly
    @requiresAuth
    def userSettings(self, auth):
        self._write("userSettings")
        return apache.OK

    @siteOnly
    @strFields(email = "", displayEmail = "",
               password1 = "", password2 = "",
               fullName = "", blurb = "")
    @requiresAuth
    def editUserSettings(self, auth, email, displayEmail, fullName,
                         password1, password2, blurb):
        if email != auth.email:
            self.user.validateNewEmail(email)
            self.user.setEmail(email)
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

    @siteOnly
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

    @siteOnly
    @strFields(title = '', hostname = '', blurb = '')
    @listFields(int, optlists = [])
    @requiresAuth
    def createProject(self, auth, title, hostname, blurb, optlists):
        errors = []
        if not title:
            error.append("You must supply a project title")
        if not hostname:
            error.append("You must supply a project hostname")
        if not errors:
            try:
                #attempt to create the project
                projectId = self.client.newProject(title, hostname, 
                                self.cfg.domainName, blurb)
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
            return self._redirect("http://%s.%s/" % (hostname, 
                                                    self.cfg.domainName) )
        else:
            kwargs = {'title': title, 'hostname': hostname, 'blurb': blurb, 'optlists': optlists}
            self._write("newProject", errors=errors, kwargs=kwargs)
            return apache.OK

    @projectOnly
    @requiresAuth
    @ownerOnly
    def projectDesc(self, auth):
        self._write("projectDesc")
        return apache.OK

    @projectOnly
    @strFields(desc = '')
    @ownerOnly
    def editProjectDesc(self, auth, desc):
        self.project.setDesc(desc)
        return self._redirect("/")

    @projectOnly
    def members(self, auth):
        self._write("members")
        return apache.OK

    @projectOnly
    def memberSettings(self, auth):
        self._write("memberSettings")
        return apache.OK

    @projectOnly
    @requiresAuth
    def adopt(self, auth):
        self.project.adopt(auth, self.cfg.MailListBaseURL, self.cfg.MailListPass)
        self._write("members")
        return apache.OK

    @projectOnly
    @strFields(username = None)
    @intFields(level = None)
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        return self._redirect("members")

    @siteOnly
    @intFields(userId = None, projectId = None, level = None)
    def addMemberById(self, auth, userId, projectId, level):
        project = self.client.getProject(projectId)
   
        if project.getUserLevel(auth.userId) != userlevels.OWNER:
            raise mint_error.PermissionDenied
    
        project.addMemberById(userId, level)
        return self._redirect("http://%s" % project.getFQDN())

    def _getUserDict(self, members):
        users = { userlevels.DEVELOPER: [],
                  userlevels.OWNER: [], }
        for userId, username, level in members:
            users[level].append((userId, username,))
        return users

    @intFields(userId = None, level = None)
    @projectOnly
    @ownerOnly
    def editMember(self, auth, userId, level):
        userDict = self._getUserDict(self.project.getMembers())
        # if there is only one owner, and that
        # owner is being changed to a non-owner, fail.
        if len(userDict[userlevels.OWNER]) == 1 and \
           userDict[userlevels.OWNER][0][0] == userId and\
           level != userlevels.OWNER:
            raise users.LastOwner
 
        self.project.updateUserLevel(userId, level)
        return self._redirect("members")

    @projectOnly
    @intFields(id = None)
    @ownerOnly
    def delMember(self, auth, id):
        userDict = self._getUserDict(self.project.getMembers())
        # if there are developers, only one owner, and that
        # owner is being deleted from the project, fail.
        if len(userDict[userlevels.DEVELOPER]) > 0 and \
           len(userDict[userlevels.OWNER]) == 1 and \
           userDict[userlevels.OWNER][0][0] == id:
            raise users.LastOwner
    
        self.project.delMemberById(id)
        if self.project.getMembers() == []:
            self.project.orphan(self.cfg.MailListBaseURL, self.cfg.MailListPass)
        return self._redirect("members")

    @projectOnly
    @intFields(userId = None)
    @ownerOnly
    def memberSettings(self, auth, userId):
        user, level = self.client.getMembership(userId, self.project.getId()) 
        self._write("memberSettings", user = user, otherUserLevel = level, userId = userId)
        return apache.OK

    @siteOnly
    @intFields(id = None)
    def userInfo(self, auth, id):
        user = self.client.getUser(id)
        self._write("userInfo", user = user,
            userProjects = self.client.getProjectsByMember(id))
        return apache.OK

    @strFields(search = "", type = None)
    @intFields(limit = 10, offset = 0, modified = 0)
    def search(self, auth, type, search, modified, limit, offset):
        if type == "Projects":
            return self.projectSearch(search, modified, limit, offset)
        # XXX disabled
        # elif type == "Users":
        #    return self.userSearch(search, limit, offset)
        elif type == "Packages":
            return self.packageSearch(search, limit, offset)
        else:
            self._write("error", shortError = "Invalid Search Type",
                error = "Invalid search type specified.")
            return apache.OK

    # XXX disabled
    # def userSearch(self, terms, limit, offset):
    #     results, count = self.client.getUserSearchResults(terms, limit, offset)
    #     self._write("searchResults", searchType = "Users", terms = terms, results = results,
    #                                  count = count, limit = limit, offset = offset,
    #                                  modified = 0)
    #     return apache.OK

    def packageSearch(self, terms, limit, offset):
        results, count = self.client.getPackageSearchResults(terms, limit, offset)
        results = [(x[0], x[1], self.client.getProject(x[2])) for x in results]
        self._write("searchResults", searchType = "Packages", terms = terms, results = results,
                                     count = count, limit = limit, offset = offset,
                                     modified = 0)
        return apache.OK
    
    def projectSearch(self, terms, modified, limit, offset):
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

    @projectOnly
    @requiresAuth
    @boolFields(confirmed = False)
    def resign(self, auth, confirmed):
        if confirmed:
            self.project.delMemberById(auth.userId)
            return self._redirect("/")
        else:
            self._write("confirm", message = "Are you sure you want to resign from this project?",
                yesLink = "resign?confirmed=1",
                noLink = "/")
        return apache.OK

    @siteOnly
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
                              **values)
        t.write(self.req, encoding = "utf-8", output = "xhtml-strict")

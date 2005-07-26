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
from urllib import unquote

from mod_python import apache
from mod_python import Cookie
from mod_python.util import FieldStorage

import repository
import versions
from deps import deps
from web import webhandler
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

class Redirect(Exception):
    def __init__(self, location):
        self.location = location

    def __str__(self):
        return "Location: %s" % self.location

def requiresAuth(func):
    def wrapper(self, **kwargs):
        if not kwargs['auth'].authorized:
            raise mint_server.PermissionDenied
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
            raise mint_server.PermissionDenied
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
                    self.project = self.client.getProjectByHostname(fullHost)
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
                return self._redirect("login")
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
        self._write("frontPage", news = news)
        return apache.OK

    @siteOnly
    def register(self, auth):
        self._write("register")
        return apache.OK

    @siteOnly
    @strFields(username = None, email = None, password = None, password2 = None, fullName = '', displayEmail = '', blurb = '')
    def processRegister(self, auth, username, fullName, email, password, password2, displayEmail, blurb):
        if password != password2:
            self._write("error", shortError = "Registration Error",
                        error = "Passwords do not match.")
        elif len(password) < 6:
            self._write("error", shortError = "Registration Error",
                        error = "Password must be 6 characters or longer.")
        else:
            try:
                self.client.registerNewUser(username, password, fullName, email,
                            displayEmail, blurb)
            except users.UserAlreadyExists:
                self._write("error", shortError = "Registration Error",
                            error = "An account with that username already exists.")
            else:
                return self._redirect("login?message=confirm")
        return apache.OK

    @siteOnly
    @strFields(message = "")
    def login(self, auth, message):
        self._write("login", message = message)
        return apache.OK

    @siteOnly
    @strFields(to = None)
    def logout(self, auth, to):
        self._clearAuth()
        return self._redirect(unquote(to))

    @strFields(username = None, password = '', submit = None, to = '/')
    def processLogin(self, auth, username, password, submit, to):
        if submit == "Log In":
            authToken = (username, password)
            client = shimclient.ShimMintClient(self.cfg, authToken)
            auth = client.checkAuth()

            if not auth.authorized:
                return self._redirect("login?message=invalid")
            else:
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

            message = "\n".join(["Your password for rpath.com has been reset to:",
                                 "",
                                 "    %s" % newpw,
                                 "",
                                 "Please log in at http://www.rpath.com/ and change",
                                 "this password as soon as possible."])

            users.sendMail(self.cfg.adminMail, "rpath.com", user.getEmail(),
                           "rpath.com forgotten password", message)
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
            return self._redirect("login?message=confirmed")
        return apache.OK 

    @intFields(sortOrder = 0, limit = 10, offset = 0)
    def projects(self, auth, sortOrder, limit, offset, submit = 0):
        results, count = self.client.getProjects(sortOrder, limit, offset)
        self._write("projects", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)
        return apache.OK

    @intFields(sortOrder = 0, limit = 10, offset = 0)
    def users(self, auth, sortOrder, limit, offset, submit = 0):
        results, count = self.client.getUsers(sortOrder, limit, offset)
        self._write("users", sortOrder=sortOrder, limit=limit, offset=offset, results=results, count=count)
        return apache.OK

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

    @requiresAuth
    @projectOnly
    @ownerOnly
    def newRelease(self, auth):
        self._write("newRelease")
        return apache.OK

    @requiresAuth
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
               desc = "", mediaSize = None)
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

    @requiresAuth
    @projectOnly
    @intFields(id = None)
    def release(self, auth, id):
        release = self.client.getRelease(id)

        try:
            trove, version, flavor = release.getTrove()
        except releases.TroveNotSet:

            return self._redirect("editRelease?releaseId=%d" % release.getId())
        else:
            refreshing = False
            job = release.getJob()

            self._write("release", release = release,
                                          name = release.getName(),
                                          trove = trove, version = versions.ThawVersion(version),
                                          flavor = deps.ThawDependencySet(flavor), job = job,
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
            # XXX confirm valid email
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
        self._write("newProject")
        return apache.OK

    @siteOnly
    @strFields(title = None, hostname = None, blurb='')
    @requiresAuth
    def createProject(self, auth, title, hostname, blurb):
        projectId = self.client.newProject(title, hostname, blurb)
        return self._redirect("http://%s.%s/" % (hostname, self.cfg.domainName) )

    @projectOnly
    @requiresAuth
    @ownerOnly
    def projectDesc(self, auth):
        self._write("projectDesc")
        return apache.OK

    @projectOnly
    @strFields(desc = None)
    @requiresAuth
    @ownerOnly
    def editProjectDesc(self, auth, desc):
        self.project.setDesc(desc)
        return self._redirect("/")

    @projectOnly
    def members(self, auth):
        self._write("members")
        return apache.OK

    @projectOnly
    @requiresAuth
    def adopt(self, auth):
        self.project.addMemberByName(auth.username, userlevels.OWNER)
        self._write("members")
        return apache.OK

    @projectOnly
    @strFields(username = None)
    @intFields(level = None)
    @ownerOnly
    def addMember(self, auth, username, level):
        self.project.addMemberByName(username, level)
        return self._redirect("members")

    @intFields(userId = None, level = None)
    @projectOnly
    @ownerOnly
    def editMember(self, auth, userId, level):
        self.project.updateUserLevel(userId, level)
        return self._redirect("members")

    @projectOnly
    @intFields(id = None)
    @requiresAuth
    @ownerOnly
    def delMember(self, auth, id):
        self.project.delMemberById(id)
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

    @strFields(search = None, type = None)
    @intFields(limit = 10, offset = 0, modified = 0)
    def search(self, auth, type, search, modified, limit, offset):
        if type == "Projects":
            return self.projectSearch(search, modified, limit, offset)
        elif type == "Users":
            return self.userSearch(search, limit, offset)
        else:
            self._write("error", shortError = "Invalid Search Type",
                error = "Invalid search type specified.")
            return apache.OK

    def userSearch(self, terms, limit, offset):
        results, count = self.client.getUserSearchResults(terms, limit, offset)
        self._write("searchResults", type="Users", terms = terms, results = results,
                                     count = count, limit = limit, offset = offset,
                                     modified = 0)
        return apache.OK

    def projectSearch(self, terms, modified, limit, offset):
        results, count = self.client.getProjectSearchResults(terms, modified, limit, offset)
        self._write("searchResults", type="Projects", terms = terms, results = results,
                                     count = count, limit = limit, offset = offset,
                                     modified = modified)
        return apache.OK



    def _write(self, template, templatePath = None, **values):
        if not templatePath:
            templatePath = self.cfg.templatePath
        path = os.path.join(templatePath, template + ".kid")
        t = kid.load_template(path)

        content = t.serialize(encoding = "utf-8", 
                              output = "xhtml-strict",
                              cfg = self.cfg,
                              auth = self.auth,
                              project = self.project,
                              userLevel = self.userLevel,
                              projectList = self.projectList,
                              toUrl = self.toUrl,
                              **values)
        self.req.write(content)

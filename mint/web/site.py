#
# Copyright (c) 2005-2009 rPath, Inc.
#

import logging
import os
import stat
from urllib import unquote
from mimetypes import guess_type

from mint import urltypes
from mint import mint_error
from mint import maintenance
from mint import shimclient
from mint.lib.unixutils import AtomicFile
from mint.session import SqlSession

from mint.web.fields import boolFields, intFields, strFields
from mint.web.decorators import requiresAdmin
from mint.web.decorators import requiresHttps
from mint.web.decorators import redirectHttps
from mint.web.decorators import redirectHttp
from mint.web.webhandler import WebHandler
from mint.web.webhandler import normPath
from mint.web.webhandler import setCacheControl
from mint.web.webhandler import HttpNotFound
from mint.web.webhandler import HttpMethodNotAllowed
from mint.web.webhandler import HttpForbidden
from mint.web.webhandler import HttpBadRequest

from conary.lib import digestlib
from conary.lib import util

log = logging.getLogger(__name__)


BUFFER=1024 * 256

class SiteHandler(WebHandler):
    def handle(self, context):
        self.__dict__.update(**context)

        path = normPath(context['cmd'])
        cmd = path.split('/')[1]

        if not cmd:
            self._redirectOldLinks()
        try:
            method = self.__getattribute__(cmd)
        except AttributeError:
            raise HttpNotFound

        if not callable(method):
            raise HttpNotFound

        return method

    @strFields(user = '', password = '')
    def pwCheck(self, auth, user, password):
        ret = 'false'
        if self.cfg.configured and (not self.cfg.SSL
                or self.req.subprocess_env.get('HTTPS', 'off') != 'off'):
            ret = str(bool(self.client.pwCheck(user, password))).lower()
        return """<auth valid="%s" />\n""" % ret

    @strFields(newUsername = '', email = '', email2 = '',
               password = '', password2 = '',
               fullName = '', displayEmail = '',
               blurb = '', tos='', privacy='')
    @redirectHttp
    @strFields(page = "")
    @intFields(step = 1)
    def help(self, auth, page, step):
        self._redirect("http://docs.rpath.com")

    @redirectHttps
    def logout(self, auth):
        self._clearAuth()
        self._redirectHttp()

    @requiresHttps
    @strFields(username = None)
    def resetPassword(self, auth, username):
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
            client = shimclient.ShimMintClient(self.cfg, authToken, self.db)
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
                self.session['authToken'] = (authToken[0], '')
                self.session['firstTimer'] = firstTimer
                self.session['firstPage'] = unquote(to)
                client.updateAccessedTime(auth.userId)
                self.session.save()

                self._redirectHttp()
        else:
            raise HttpNotFound

    def loginFailed(self, auth):
        if isinstance(self.session, SqlSession):
            c = self.session.make_cookie()
            c.expires = 0
            self.req.err_headers_out.add('Set-Cookie', str(c))
            setCacheControl(self.req, strict=True)
        return self._write('error', shortError = "Login Failed",
            error = 'You cannot log in because your browser is blocking '
            'cookies to this site.')

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
                redirectUrl = "/images/%s/%d/%s" % (project.hostname, build.id,
                        os.path.basename(filename))

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
            return ""
        if redirectUrl:
            self._redirect(redirectUrl)
        else:
            raise HttpNotFound

    @redirectHttps
    def maintenance(self, auth, *args, **kwargs):
        mode = maintenance.getMaintenanceMode(self.cfg)
        if mode == maintenance.NORMAL_MODE:
            # Maintenance is over, redirect to the homepage
            self._redirectHttp()
        elif mode == maintenance.EXPIRED_MODE:
            # rBuilder is disabled due to expired entitlement
            return self._write("maintenance", reason="expired")
        elif auth.admin:
            # Admins are bounced to the admin page
            self._redirectHttp("administer")
        else:
            # Everyone else gets the maintenance notice
            return self._write("maintenance", reason="maintenance")

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
                self._addErrors("You cannot close your account from this "
                    "interface.")
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
            self._addErrors("Please select a valid user adminstration action "
                "from the menu.")

        if deletedUser:
            return self._redirectHttp()
        else:
            return self._redirectHttp("userInfo?id=%d" % (userId,))
    def uploadBuild(self, auth):
        method = self.req.method.upper()
        if method != "PUT":
            raise HttpMethodNotAllowed

        client = shimclient.ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db)

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

        targetFn = os.path.join(self.cfg.imagesPath, project.hostname,
                str(buildId), fileName)
        util.mkdirChain(os.path.dirname(targetFn))
        fObj = AtomicFile(targetFn, 'wb', prefix='img-', suffix='.tmp')
        ctx = digestlib.sha1()

        try:
            copied = util.copyfileobj(self.req, fObj, digest=ctx)
        except IOError, err:
            log.warning("IOError during upload of %s: %s", targetFn, str(err))
            raise HttpBadRequest

        if 'content-length' in self.req.headers_in:
            expected = long(self.req.headers_in['content-length'])
            if copied != expected:
                log.warning("Expected %d bytes but got %d bytes for "
                        "uploaded file %s; discarding", expected, copied,
                        targetFn)
                return ''

        # Validate SHA1 trailer (or header) if it is present.
        if 'content-sha1' in self.req.headers_in:
            expected = self.req.headers_in['content-sha1'].decode('base64')
            actual = ctx.digest()
            if expected != actual:
                log.warning("SHA-1 mismatch on uploaded file %s; "
                        "discarding.", targetFn)
                return ''

        fObj.commit(sync=False)
        return ''

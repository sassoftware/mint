#
# Copyright (c) SAS Institute Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


import errno
import logging
import os
from urllib import unquote
from webob import exc as web_exc

from mint import urltypes
from mint import mint_error
from mint import shimclient
from mint.lib.unixutils import AtomicFile

from mint.web.fields import boolFields, intFields, strFields
from mint.web.decorators import requiresAdmin
from mint.web.decorators import requiresHttps
from mint.web.webhandler import WebHandler
from mint.web.webhandler import normPath

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
            raise web_exc.HTTPNotFound()

        if not callable(method):
            raise web_exc.HTTPNotFound()

        return method

    @strFields(user = '', password = '')
    def pwCheck(self, auth, user, password):
        ret = 'false'
        if self.cfg.configured and (not self.cfg.SSL
                or self.req.scheme == 'https'):
            ret = str(bool(self.client.pwCheck(user, password))).lower()
        return """<auth valid="%s" />\n""" % ret

    @strFields(newUsername = '', email = '', email2 = '',
               password = '', password2 = '',
               fullName = '', displayEmail = '',
               blurb = '', tos='', privacy='')
    @strFields(page = "")
    @intFields(step = 1)
    def help(self, auth, page, step):
        self._redirect("http://docs.rpath.com")

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

            if not auth.authorized:
                raise mint_error.InvalidLogin
            else:
                self.session['authToken'] = (authToken[0], '')
                self.session['firstPage'] = unquote(to)
                self.session.save()

                self._redirectHttp()
        else:
            raise web_exc.HTTPNotFound()

    @intFields(fileId = 0, urlType = urltypes.LOCAL)
    def downloadImage(self, auth, fileId, urlType):
        reqFilename = None
        try:
            if not fileId:
                cmds = self.cmd.split('/')
                fileId = int(cmds[1])
                reqFilename = cmds[2]
        except ValueError:
            raise web_exc.HTTPNotFound()

        # Screen out UrlTypes that are not visible, except for urltypes.LOCAL,
        # which is ALWAYS visible.
        if not (urlType == urltypes.LOCAL \
                or urlType in self.cfg.visibleUrlTypes):
            raise web_exc.HTTPNotFound()

        try:
            buildId, idx, title, fileUrls = self.client.getFileInfo(fileId)
        except mint_error.FileMissing:
            raise web_exc.HTTPNotFound()

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

        if urlType == urltypes.LOCAL:
            if overrideRedirect:
                redirectUrl = overrideRedirect
            elif filename:
                # Don't pass through bad filenames if they are specified in
                # the request.
                if reqFilename and os.path.basename(filename) != reqFilename:
                    raise web_exc.HTTPNotFound()

                if not os.path.exists(filename):
                    raise web_exc.HTTPNotFound()

                build = self.client.getBuild(buildId)
                project = self.client.getProject(build.projectId) 
                redirectUrl = "/images/%s/%d/%s" % (project.hostname, build.id,
                        os.path.basename(filename))
        if redirectUrl:
            self._redirect(redirectUrl)
        else:
            raise web_exc.HTTPNotFound()

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
            raise web_exc.HTTPMethodNotAllowed(allow='PUT')

        client = shimclient.ShimMintClient(self.cfg,
                (self.cfg.authUser, self.cfg.authPass), self.db)

        buildId, fileName = self.req.path_info.split("/")[-2:]
        build = client.getBuild(int(buildId))
        project = client.getProject(build.projectId)

        # make sure the hash we receive from the slave matches
        # the hash we gave the slave in the first place.
        # this prevents slaves from overwriting arbitrary files
        # in the finished images directory.
        if not auth.admin:
            outputToken = self.req.headers.get('X-rBuilder-OutputToken')
            if outputToken != build.getDataValue('outputToken', validate = False):
                raise web_exc.HTTPForbidden()

        targetFn = os.path.join(self.cfg.imagesPath, project.hostname,
                str(buildId), fileName)
        util.mkdirChain(os.path.dirname(targetFn))
        fObj = AtomicFile(targetFn, 'wb+', prefix='img-', suffix='.tmp')
        ctx = digestlib.sha1()

        inFile = None
        if 'x-uploaded-file' in self.req.headers:
            # The frontend proxy has already saved the request body to a
            # temporary location, so first try to rename it into place.
            try:
                os.rename(self.req.headers['x-uploaded-file'], fObj.name)
            except OSError, err:
                if err.errno != errno.EXDEV:
                    raise
                # Upload dir is on a different filesystem.
                inFile = open(self.req.headers['x-uploaded-file'], 'rb')
        else:
            # No offloading was done. Copy from the request body.
            inFile = self.req.body_file

        if inFile:
            # Copy and digest simultaneously
            try:
                copied = util.copyfileobj(self.req.body_file, fObj, digest=ctx)
            except IOError, err:
                log.warning("IOError during upload of %s: %s", targetFn, str(err))
                raise web_exc.HTTPBadRequest()
        else:
            # Just digest
            with open(fObj.name) as inFile:
                while True:
                    data = inFile.read(1024)
                    if not data:
                        break
                    ctx.update(data)

        if 'content-length' in self.req.headers:
            expected = long(self.req.headers['content-length'])
            if copied != expected:
                log.warning("Expected %d bytes but got %d bytes for "
                        "uploaded file %s; discarding", expected, copied,
                        targetFn)
                return ''

        fObj.commit(sync=False)
        # Write out digest, to be validated when the jobslave posts the final
        # image file list.
        fObj = AtomicFile(targetFn + '.sha1', 'w')
        print >> fObj, ctx.hexdigest()
        fObj.commit()
        return ''

    def conaryrc(self, auth):
        out = ''
        if self.req.params.get('repositoryMap') != 'no':
            repoMap = {}
            for handle in self.reposShim.iterRepositories('NOT disabled'):
                repoMap[handle.fqdn] = handle.getURL()
            for name, url in sorted(repoMap.items()):
                out += 'repositoryMap %s %s\n' % (name, url)
        if self.req.params.get('proxyMap') != 'no':
            proxy = 'conarys://' + self.req.application_url.split('://')[-1]
            out += 'proxyMap * %s\n' % proxy
        self.response.content_type = 'text/plain'
        return out

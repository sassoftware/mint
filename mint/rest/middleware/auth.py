#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import base64
from conary.lib import util

from mod_python import Cookie

from restlib.response import Response
from mint import maintenance
from mint import shimclient
from mint.rest.api import models
from mint.rest.modellib import converter
from mint.session import SqlSession
from mint.rest import errors

# Decorator for public (unauthenticated) methods/functions
def public(deco):
    deco.public = True
    return deco

# Decorator for methods/functions that require admin
def admin(deco):
    deco.admin = True
    return deco

# Decorator for internal methods/functions. Access should only be allowed from
# localhost
def internal(deco):
    deco.internal = True
    return deco


def tokenRequired(func):
    """
    Mark an image-build-related API function as requiring an authentication
    token in the HTTP headers. The token will be placed in
    C{request.imageToken}.
    """
    func.tokenRequired = True
    return func


def noDisablement(method):
    """
    Decorator for methods that should work even when the rBuilder's
    authorization is invalid/expired.
    """
    method.dont_disable = True
    return method


class AuthenticationCallback(object):

    def __init__(self, cfg, db, controller):
        self.cfg = cfg
        self.db = db
        self.controller = controller

    def getAuth(self, request):
        if not 'Authorization' in request.headers:
            return None
        type, user_pass = request.headers['Authorization'].split(' ', 1)
        try:
            user_name, password = base64.decodestring(user_pass).split(':', 1)
            password = util.ProtectedString(password)
            return (user_name, password)
        except:
            raise errors.AuthHeaderError

    def getCookieAuth(self, request):
        # the pysid cookie contains the session reference that we can use to
        # look up the proper credentials
        # we need the underlying request object since restlib doesn't
        # have support for cookies yet.
        cfg = self.cfg
        req = request._req
        anonToken = ('anonymous', 'anonymous')
        try:
            if cfg.cookieSecretKey:
                cookies = Cookie.get_cookies(req, Cookie.SignedCookie,
                                             secret = cfg.cookieSecretKey)
            else:
                cookies = Cookie.get_cookies(req, Cookie.Cookie)
        except:
            cookies = {}
        if 'pysid' not in cookies:
            return None

        sid = cookies['pysid'].value

        sessionClient = shimclient.ShimMintClient(cfg,
                (cfg.authUser, cfg.authPass), db=self.db.db.db)

        session = SqlSession(req, sessionClient,
            sid = sid,
            secret = cfg.cookieSecretKey,
            timeout = 86400,
            lock = False)
        return session.get('authToken', None)

    def _checkAuth(self, authToken):
        mintClient = shimclient.ShimMintClient(self.cfg, authToken,
                db=self.db.db.db)
        mintAuth = mintClient.checkAuth()
        if mintAuth:
            return mintClient, mintAuth
        return None, None


    def processRequest(self, request):
        # Determine authentication.  We have two mechanisms
        # for checking authentication.
        # If someone has a good basic auth information but a bad
        # cookie, we want to let them through and then update
        # their cookie.
        # If they have a good cookie but bad auth information,
        # we want to let them through as well.
        # basic auth overrides cookie if they are both provided.
        mintClient = None
        mintAuth = None
        cookieToken = None
        basicToken = self.getAuth(request)
        if basicToken:
            mintClient, mintAuth = self._checkAuth(basicToken)
            request.auth = basicToken
        if not mintAuth:
            cookieToken = self.getCookieAuth(request)
            if cookieToken:
                mintClient, mintAuth = self._checkAuth(cookieToken)
                request.auth = cookieToken

        if not mintAuth:
            # No authentication was successful.
            request.auth = request.mintClient = request.mintAuth = None
            return

        request.mintClient = mintClient
        request.mintAuth = mintAuth
        self.db.setAuth(mintAuth, request.auth)
        self.db.mintClient = mintClient

        if self.db.siteAuth:
            self.db.siteAuth.refresh()

    def checkDisablement(self, request, viewMethod):
        """
        Check whether the rBuilder is disabled for maintenance or
        authentication reasons. If it is, and the method being
        invoked isn't flagged as always available, raise a fault.
        """
        if not getattr(viewMethod, 'dont_disable', False):
            mode = maintenance.getMaintenanceMode(self.cfg)
            if mode == maintenance.NORMAL_MODE:
                return

            code = 503
            if mode == maintenance.EXPIRED_MODE:
                content = ("The rBuilder's entitlement has expired.\n\n"
                        "Please navigate to the rBuilder homepage for "
                        "more information.\n")
                error = 'site-disabled'
            elif mode == maintenance.LOCKED_MODE:
                content = ("The rBuilder is currently in maintenance mode."
                        "\n\nPlease contact your site administrator for more "
                        "information.\n")
                error = 'maintenance-mode'

            # Flex can't get headers from error responses in Firefox
            isFlash = 'HTTP_X_FLASH_VERSION' in request.headers

            if not getattr(request, 'contentType', None):
                request.contentType = 'text/plain'
                request.responseType = 'xml'

            if isFlash or request.contentType != 'text/plain':
                fault = models.Fault(code=code, message=content)
                content = converter.toText(request.responseType, fault,
                        self.controller, request)
                if isFlash:
                    code = 200
            return Response(content, content_type=request.contentType,
                    status=code, headers={'X-rBuilder-Error': error})

    def processMethod(self, request, viewMethod, args, kwargs):
        response = self.checkDisablement(request, viewMethod)
        if response:
            return response

        if (getattr(viewMethod, 'internal', False)
                and request.remote[0] != '127.0.0.1'):
            # Request to an internal API from an external IP address
            return Response(status=404)

        if getattr(viewMethod, 'tokenRequired', False):
            imageToken = request.headers.get('X-rBuilder-OutputToken')
            if not imageToken:
                return Response(status=403)
            request.imageToken = imageToken
            return None

        if getattr(viewMethod, 'admin', False):
            if request.mintAuth is not None:
                if request.mintAuth.admin:
                    return None
                else:
                    return Response(status=401,
                             headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})
            else:
                return Response(status=403)

        # require authentication
        if (not getattr(viewMethod, 'public', False)
                and request.mintAuth is None):
            if 'HTTP_X_FLASH_VERSION' in request.headers:
                return Response(status=403)
            return Response(status=401,
                     headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})

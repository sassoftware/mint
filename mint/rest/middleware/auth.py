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

from restlib.response import Response
from mint import maintenance
from mint import shimclient
from mint.rest.api import models
from mint.rest.modellib import converter


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

    def _checkAuth(self, authToken):
        mintClient = shimclient.ShimMintClient(self.cfg, authToken,
                db=self.db.db.db)
        mintAuth = mintClient.checkAuth()
        if mintAuth:
            return mintClient, mintAuth
        return None, None

    def processRequest(self, request):
        mintClient = None
        mintAuth = None
        authToken = request._req.environ['mint.authToken'][:2]
        if authToken:
            mintClient, mintAuth = self._checkAuth(authToken)
            request.auth = authToken
        if not mintAuth or not mintAuth.authorized:
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

        remote = request.remote
        if isinstance(remote, (list, tuple)):
            remote = remote[0]
        if getattr(viewMethod, 'internal', False) and remote not in (
                '127.0.0.1', '::1', '::ffff:127.0.0.1'):
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
                    # TODO: new way is to wrap these as XML faults and return 200 to Flash
                    if 'HTTP_X_FLASH_VERSION' in request.headers:
                        return Response('Unauthorized', status=403)
                    return Response(status=401,
                             headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})
            else:
                return Response(status=403)

        # require authentication
        if (not getattr(viewMethod, 'public', False)
                and request.mintAuth is None):
            if 'HTTP_X_FLASH_VERSION' in request.headers:
                # TODO: new way is to wrap these as XML faults and return 200 to Flash
                return Response('Unauthorized', status=403)
            return Response(status=401,
                     headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})

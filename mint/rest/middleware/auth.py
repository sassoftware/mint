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
from mint import shimclient


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

    def processMethod(self, request, viewMethod, args, kwargs):
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
                    if 'HTTP_X_FLASH_VERSION' in request.headers or 'X-Wrap-Response-Codes' in request.headers:
                        return Response('Unauthorized', status=403)
                    return Response(status=401,
                             headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})
            else:
                return Response(status=403)

        # require authentication
        if (not getattr(viewMethod, 'public', False)
                and request.mintAuth is None):
            if 'HTTP_X_FLASH_VERSION' in request.headers or 'X-Wrap-Response-Codes' in request.headers:
                # TODO: new way is to wrap these as XML faults and return 200 to Flash
                return Response('Unauthorized', status=403)
            return Response(status=401,
                     headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})

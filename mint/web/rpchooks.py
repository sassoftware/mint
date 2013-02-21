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

import xmlrpclib
from conary.lib import util
from conary.repository import errors
from webob import exc as web_exc

from mint import mint_error
from mint import server
from mint.web.webhandler import getHttpAuth


def rpcHandler(context):
    req = context.req
    # only handle POSTs
    if req.method.upper() != 'POST':
        raise web_exc.HTTPMethodNotAllowed(allow='POST')
    if req.content_type != 'text/xml':
        raise web_exc.HTTPBadRequest()
    authToken = getHttpAuth(req)

    if type(authToken) is list:
        authToken = authToken[0:2] # throw away entitlement
    # instantiate a MintServer
    srvr = server.MintServer(context.cfg, allowPrivate=True, req=req,
            db=context.db)
    stream = req.body_file
    encoding = req.headers.get('Content-Encoding', 'identity')
    if encoding == 'deflate':
        stream = util.decompressStream(stream)
        stream.seek(0)
    elif encoding != 'identity':
        raise web_exc.HTTPBadRequest()
    (args, method) = util.xmlrpcLoad(stream)

    # coax parameters into something MintServer likes
    params = [method, authToken, args]

    # go for it; return 403 if permission is denied
    try:
        # result is (isError, returnValues)
        result = srvr.callWrapper(*params)
    except (errors.InsufficientPermission, mint_error.PermissionDenied):
        return context.responseFactory(
                "<h1>Forbidden</h1>\n"
                "<p>Access denied by the server.</p>\n",
                status='403 Forbidden',
                content_type='text/html')

    # create a response
    resp = xmlrpclib.dumps((result,), methodresponse=1)
    return context.responseFactory(content_type='text/xml', body=resp)

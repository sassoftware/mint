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


import json
import xmlrpclib
from conary.lib import util
from conary.repository import errors
from webob import exc as web_exc

from mint import mint_error
from mint import server


def rpcHandler(context):
    req = context.req
    # only handle POSTs
    if req.method.upper() != 'POST':
        raise web_exc.HTTPMethodNotAllowed(allow='POST')
    if req.content_type == 'text/xml':
        kind = 'xml'
    elif req.content_type == 'application/x-json':
        kind = 'json'
    else:
        raise web_exc.HTTPBadRequest()
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
    if kind == 'xml':
        (args, method) = util.xmlrpcLoad(stream)
    else:
        (method, args) = json.load(stream)

    # coax parameters into something MintServer likes
    params = [method, context.authToken, args]

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
    if kind == 'xml':
        resp = xmlrpclib.dumps((result,), methodresponse=1)
    else:
        resp = json.dumps(result[1])
    return context.responseFactory(content_type=req.content_type, body=resp)

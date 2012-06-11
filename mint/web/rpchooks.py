#
# Copyright (c) 2005-2009 rPath, Inc.
#
# All Rights Reserved
#
import logging
import json
import sys
import xmlrpclib

from mod_python import apache

from mint import config
from mint import mint_error
from mint import server
from mint import maintenance
from mint.lib import mintutils
from mint.logerror import logWebErrorAndEmail
from mint.web.webhandler import getHttpAuth

from conary import dbstore
from conary.lib import coveragehook
from conary.repository import errors


def rpcHandler(context):
    return _rpcHandler(context.req, context.db, context.cfg)


def _rpcHandler(req, db, cfg, pathInfo = None):
    mintutils.setupLogging(consoleLevel=logging.INFO, consoleFormat='apache')

    maintenance.enforceMaintenanceMode(cfg)
    isJSONrpc = isXMLrpc = allowPrivate = False

    # only handle POSTs
    if req.method.upper() != 'POST':
        return apache.HTTP_METHOD_NOT_ALLOWED

    if "allowPrivate" in req.get_options():
        allowPrivate = req.get_options()['allowPrivate']
    elif "xmlrpc-private" in req.uri.split("/")[1]:
        allowPrivate = True

    if req.headers_in['Content-Type'].startswith('text/xml'):
        isXMLrpc = True
    elif req.headers_in['Content-Type'].startswith('application/x-json'):
        isJSONrpc = True
    else:
        return apache.HTTP_BAD_REQUEST

    authToken = getHttpAuth(req)

    if type(authToken) is list:
        authToken = authToken[0:2] # throw away entitlement
    # instantiate a MintServer
    srvr = server.MintServer(cfg, allowPrivate=allowPrivate, req=req, db=db)

    # switch on XML/JSON here
    if isXMLrpc:
        (args, method) = xmlrpclib.loads(req.read())
    if isJSONrpc:
        (method, args) = json.loads(req.read())

    # coax parameters into something MintServer likes
    params = [method, authToken, args]

    # go for it; return 403 if permission is denied
    try:
        # result is (isError, returnValues)
        result = srvr.callWrapper(*params)
    except (errors.InsufficientPermission, mint_error.PermissionDenied):
        return apache.HTTP_FORBIDDEN

    # create a response
    if isXMLrpc:
        resp = xmlrpclib.dumps((result,), methodresponse=1)
        req.content_type = "text/xml"
    elif isJSONrpc:
        resp = json.dumps(result[1])
        req.content_type = "application/x-json"

    # write repsonse
    try:
        req.write(resp)
    except IOError, err:
        # Client went away
        req.log_error('Error writing to client: %s' % err)
    return apache.OK

def handler(req):
    coveragehook.install()
    cfg = config.getConfig(req.filename)
    db = dbstore.connect(cfg.dbPath, cfg.dbDriver)

    try:
        try:
            return _rpcHandler(req, db, cfg)
        except:
            e_type, e_value, e_tb = sys.exc_info()
            logWebErrorAndEmail(req, cfg, e_type, e_value, e_tb, 'XMLRPC handler')
            del e_tb
            return apache.HTTP_INTERNAL_SERVER_ERROR
    finally:
        db.close()
        logging.shutdown()

#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

from mod_python import Cookie
from conary.lib import coveragehook
from mint import maintenance
from mint import shimclient
from mint.session import SqlSession

from catalogService import handler_apache

def getAuthFromSession(req, cfg):
    # the pysid cookie contains the session reference that we can use to
    # look up the proper credentials
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
        return anonToken

    sid = cookies['pysid'].value

    sessionClient = shimclient.ShimMintClient(cfg, (cfg.authUser, cfg.authPass))

    session = SqlSession(req, sessionClient,
        sid = sid,
        secret = cfg.cookieSecretKey,
        timeout = 86400,
        lock = False)
    return session.get('authToken', anonToken)

def catalogHandler(req, cfg, pathInfo = None):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(cfg)

    # the leading portion of the URI in an rBuilder context. catalog-service
    # string substitutes, so leading and trailing slashes aren't needed.
    topLevel = 'catalog'

    client_address = req.connection.remote_addr
    server = type('Server', (object,), {'server_port': req.server.port})
    aReq = handler_apache.ApacheRequest(req)
    hdlr = handler_apache.ApacheHandler(topLevel, aReq, client_address, server)
    hdlr.mintCfg = cfg

    auth = tuple(getAuthFromSession(req, cfg)[:2])
    hdlr.setAuthHeader(*auth)

    hdlr.handleApacheRequest()
    return 0

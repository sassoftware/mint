#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import os

from mod_python import Cookie
from conary.lib import coveragehook
from mint import maintenance
from mint import shimclient
from mint.session import SqlSession

from catalogService import handler_apache
from catalogService.rest import auth


class SessionAuthenticationCallback(auth.AuthenticationCallback):
    def __init__(self, storageConfig, mintConfig, mintDb):
        self.mintConfig = mintConfig
        self.mintDb = mintDb
        auth.AuthenticationCallback.__init__(self, storageConfig)

    def getMintConfig(self):
        return self.mintConfig

    def getAuth(self, request):
        # the pysid cookie contains the session reference that we can use to
        # look up the proper credentials
        # we need the underlying request object since restlib doesn't
        # have support for cookies yet.
        req = request._req
        cfg = self.mintConfig
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

        sessionClient = shimclient.ShimMintClient(cfg,
                (cfg.authUser, cfg.authPass), self.mintDb)

        session = SqlSession(req, sessionClient,
            sid = sid,
            secret = cfg.cookieSecretKey,
            timeout = 86400,
            lock = False)
        return session.get('authToken', anonToken)


class RbuilderCatalogRESTHandler(handler_apache.ApacheRESTHandler):
    def __init__(self, *args, **kw):
        self.mintConfig = kw.pop('mintConfig')
        handler_apache.ApacheRESTHandler.__init__(self, *args, **kw)

    def addAuthCallback(self):
        self.handler.addCallback(SessionAuthenticationCallback(self.storageConfig, self.mintConfig))

def catalogHandler(req, db, cfg, pathInfo = None):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(cfg)
    # the leading portion of the URI in an rBuilder context. catalog-service
    # string substitutes, so leading and trailing slashes aren't needed.
    topLevel = os.path.join(cfg.basePath, 'catalog')
    storagePath = os.path.join(cfg.dataPath, 'catalog')
    handler = RbuilderCatalogRESTHandler(topLevel, storagePath,
                                         mintConfig=cfg)
    return handler.handle(req)

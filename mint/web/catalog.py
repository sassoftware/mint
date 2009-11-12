#
# Copyright (c) 2008 rPath, Inc.
#
# All Rights Reserved
#

import base64
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
            return self.getBasicAuth(request) or anonToken

        sid = cookies['pysid'].value

        sessionClient = shimclient.ShimMintClient(cfg,
                (cfg.authUser, cfg.authPass), self.mintDb)

        session = SqlSession(req, sessionClient,
            sid = sid,
            secret = cfg.cookieSecretKey,
            timeout = 86400,
            lock = False)
        return session.get('authToken', anonToken)

    @classmethod
    def getBasicAuth(cls, request):
        headers = request.headers
        auth = headers.get('Authorization')
        if not auth:
            return None
        info = auth.split(' ', 1)
        if info[0] != 'Basic' or len(info) != 2:
            return None

        try:
            user_pass = base64.b64decode(info[1])
        except TypeError:
            return None
        user_pass = user_pass.split(':', 1)
        if len(user_pass) != 2:
            return None
        return tuple(user_pass)


class RbuilderCatalogRESTHandler(handler_apache.ApacheRESTHandler):
    def __init__(self, *args, **kw):
        self.mintConfig = kw.pop('mintConfig')
        self.mintDb = kw.pop('mintDb')
        handler_apache.ApacheRESTHandler.__init__(self, *args, **kw)

    def addAuthCallback(self):
        self.handler.addCallback(SessionAuthenticationCallback(
            self.storageConfig, self.mintConfig, self.mintDb))


def catalogHandler(context):
    coveragehook.install()
    maintenance.enforceMaintenanceMode(context.cfg)
    # the leading portion of the URI in an rBuilder context. catalog-service
    # string substitutes, so leading and trailing slashes aren't needed.
    topLevel = os.path.join(context.cfg.basePath, 'catalog')
    storagePath = os.path.join(context.cfg.dataPath, 'catalog')
    handler = RbuilderCatalogRESTHandler(topLevel, storagePath,
            mintConfig=context.cfg, mintDb=context.db)
    return handler.handle(context.req)

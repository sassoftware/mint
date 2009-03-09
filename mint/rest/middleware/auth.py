#!/usr/bin/python
#
# Copyright (c) 2009 rPath, Inc.
#
# All Rights Reserved
#

import base64

from mod_python import Cookie

from restlib.response import Response
from mint import config
from mint import shimclient
from mint.session import SqlSession

# Decorator for public (unauthenticated) methods/functions
def public(deco):
    deco.public = True
    return deco

class AuthenticationCallback(object):

    def __init__(self, cfg, db):
        self.cfg = cfg
        self.db = db

    def getAuth(self, request):
        if not 'Authorization' in request.headers:
            return None
        type, user_pass = request.headers['Authorization'].split(' ', 1)
        user_name, password = base64.decodestring(user_pass).split(':', 1)
        return (user_name, password)

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

        sessionClient = shimclient.ShimMintClient(cfg, (cfg.authUser, 
                                                        cfg.authPass))

        session = SqlSession(req, sessionClient,
            sid = sid,
            secret = cfg.cookieSecretKey,
            timeout = 86400,
            lock = False)
        return session.get('authToken', None)

    def processRequest(self, request):
        request.mintClient = None
        request.mintAuth = None
        authToken = self.getAuth(request)
        if not authToken:
            authToken = self.getCookieAuth(request)
        request.auth = authToken

        if request.auth is None:
            # Not authenticated
            return

        mintClient = shimclient.ShimMintClient(self.cfg, authToken)
        mintAuth = mintClient.checkAuth()
        if not mintAuth:
            # Bad auth info
            return

        request.mintClient = mintClient
        request.mintAuth = mintAuth
        self.db.setAuth(mintAuth, authToken)
        self.db.mintClient = mintClient

    def processMethod(self, request, viewMethod, args, kwargs):
        if getattr(viewMethod, 'public', None) or request.mintAuth is not None:
            return
        # require authentication
        return Response(status=401, 
             headers={'WWW-Authenticate' : 'Basic realm="rBuilder"'})

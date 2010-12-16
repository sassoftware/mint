#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#
from mod_python import apache
from mod_python import Cookie
from mod_python.Session import BaseSession

COOKIE_NAME = 'pysid'

class SqlSession(BaseSession):
    """An implementation of mod_python's Session support for an sqlite backend."""
    def __init__(self, req, client, sid = 0,
                 secret = None, timeout = 0, lock = 1):
        self._client = client

        BaseSession.__init__(self, req, sid = sid, secret = secret,
                             timeout = timeout, lock = lock)

    def make_cookie(self):
        if self._secret:
            c = Cookie.SignedCookie(COOKIE_NAME, self._sid,
                                    secret = self._secret)
        else:
            c = Cookie.Cookie(COOKIE_NAME, self._sid)

        c.path = '/'
        c.secure = True
        return c
    
    def do_cleanup(self):
        self._req.register_cleanup(sql_cleanup, self._client)

    def do_load(self):
        return self._client.loadSession(str(self._sid))

    def do_save(self, data):
        self._client.saveSession(str(self._sid), data)

    def do_delete(self):
        self._client.deleteSession(str(self._sid))

    def invalidate(self):
        """ Override the BaseSession invalidate() to make sure the cookies
            survive a redirect. """
        c = self.make_cookie()
        c.expires = 0
        Cookie.add_cookie(self._req, c)
        self._req.err_headers_out.add('Set-Cookie', str(c))
        self.delete()
        self._invalid = 1

def sql_cleanup(client):
    client.cleanupSessions()

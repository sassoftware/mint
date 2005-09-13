#
# Copyright (c) 2005 rPath, Inc.
#
# All Rights Reserved
#
from mod_python import apache
from mod_python.Session import BaseSession
from mod_python import Cookie

COOKIE_NAME = 'pysid'

class SqlSession(BaseSession):
    """An implementation of mod_python's Session support for an sqlite backend."""
    def __init__(self, req, client, sid = 0,
                 secret = None, timeout = 0, lock = 1, domain = None):
        self._client = client
        self._domain = domain

        BaseSession.__init__(self, req, sid = sid, secret = secret,
                             timeout = timeout, lock = lock)

    def make_cookie(self):
        if self._secret:
            c = Cookie.SignedCookie(COOKIE_NAME, self._sid,
                                    secret=self._secret,
                                    domain = self._domain)
        else:
            c = Cookie.Cookie(COOKIE_NAME, self._sid, domain = self._domain)

        c.path = '/'
        return c
    
    def do_cleanup(self):
        self._req.register_cleanup(sql_cleanup, self._client)
        self._req.log_error("SqlSession: registered database cleanup.",
                            apache.APLOG_NOTICE)

    def do_load(self):
        return self._client.loadSession(self._sid)

    def do_save(self, data):
        self._client.saveSession(self._sid, data)

    def do_delete(self):
        self._client.deleteSession(self._sid)

def sql_cleanup(client):
    client.cleanupSessions()

#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#

import unittest

from mint import config
from mint import mint_error
from mint.lib import database
from mint import userlevels
from mint.web import decorators, webhandler
from mint.users import Authorization

class FakeReq:
    subprocess_env = {}
    headers_in = {}
    unparsed_uri = '/hello'
    parsed_uri = ['http', '', 'user', 'pass', 'www.example.com', 80, '/hello', '', '']
    hostname = 'www.example.com'
    method = "GET"

    def __init__(self, ssl = False):
        self.subprocess_env['HTTPS'] = ssl and "on" or "off"
        self.headers_in['host'] = self.hostname


def dummy(*args, **kwargs):
    return True


class WebDecoratorTest(unittest.TestCase): 
    def setUp(self):
        unittest.TestCase.setUp(self)
        self.cfg = config.MintConfig()
        self.cfg.siteDomainName = "insecure.com:8080"
        self.cfg.secureHost = "www.secure.com:8443"
        self.cfg.namespace = 'yournamespace'

    def _redirect(self, *args, **kwargs):
        return args[0]

    def testRequiresHttps(self):
        self.req = FakeReq()
        w = decorators.requiresHttps(dummy)
        assert(w(self) == True)

        self.req = FakeReq(ssl = False)
        self.cfg.SSL = True
        w = decorators.requiresHttps(dummy)
        self.assertRaises(mint_error.PermissionDenied, w, self)

    def testRedirectHttp(self):
        self.req = FakeReq(ssl = False)
        w = decorators.redirectHttp(dummy)
        assert(w(self) == True)

        self.req = FakeReq(ssl = True)
        self.cfg.SSL = True
        w = decorators.redirectHttp(dummy)
        self.assertEquals(w(self), "http://www.example.com:8080/hello")

    def testRedirectHttps(self):
        self.req = FakeReq(ssl = True)
        w = decorators.redirectHttps(dummy)
        assert(w(self) == True)

        self.req = FakeReq(ssl = False)
        self.cfg.SSL = True
        w = decorators.redirectHttps(dummy)
        self.assertEquals(w(self), "https://www.example.com:8443/hello")

        self.req.hostname = "www.secure.com"
        self.assertEquals(w(self), "https://www.secure.com:8443/hello")

    def testRequiresAdmin(self):
        auth = Authorization(admin = False)
        w = decorators.requiresAdmin(dummy)
        self.assertRaises(mint_error.PermissionDenied, w, self, auth = auth)

        auth.admin = True
        assert(w(self, auth = auth))

    def testRequiresAuth(self):
        auth = Authorization(authorized = False)
        w = decorators.requiresAuth(dummy)
        self.assertRaises(mint_error.PermissionDenied, w, self, auth = auth)

        auth.authorized= True
        assert(w(self, auth = auth))

    def testOwnerOnly(self):
        self.project = None

        w = decorators.ownerOnly(dummy)
        self.assertRaises(database.ItemNotFound, w, self)

        self.project = 1

        # non member, not admin
        self.userLevel = userlevels.NONMEMBER
        self.auth = Authorization(admin = False)
        self.assertRaises(mint_error.PermissionDenied, w, self, auth = self.auth)

        # owner, not admin
        self.userLevel = userlevels.OWNER
        self.auth = Authorization(admin = False)
        assert(w(self, auth = self.auth))

        # admin
        self.auth = Authorization(admin = True)
        assert(w(self, auth = self.auth))

    def testWritersOnly(self):
        self.project = None

        w = decorators.writersOnly(dummy)
        self.assertRaises(database.ItemNotFound, w, self)

        self.project = 1

        # non member, not admin
        self.userLevel = userlevels.NONMEMBER
        self.auth = Authorization(admin = False)
        self.assertRaises(mint_error.PermissionDenied, w, self, auth = self.auth)

        # developer, not admin
        self.userLevel = userlevels.DEVELOPER
        self.auth = Authorization(admin = False)
        assert(w(self, auth = self.auth))

        # admin
        self.auth = Authorization(admin = True)
        assert(w(self, auth = self.auth))

    def testPostOnly(self):
        w = decorators.postOnly(dummy)

        self.req = FakeReq()
        self.assertRaises(webhandler.HttpForbidden, w, self)

        self.req.method = "POST"
        assert(w(self))



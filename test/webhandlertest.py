#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import testsuite
import unittest
testsuite.setup()

from mint.web import webhandler

class FakeConfig(object):
    __slots__ = [ 'basePath', 'hostname', 'externalDomainName' ]

    def __init__(self, basepath, hostname, extdomainname):
        self.basePath = basepath
        self.hostname = hostname
        self.externalDomainName = extdomainname


class FakeRequest(object):
    __slots__ = [ 'err_headers_out', 'hostname', 'headers_in',
            'headers_out', 'method', 'error_logged' ]

    def __init__(self, hostname, methodname, filename):
        self.method = methodname
        self.hostname = hostname
        self.headers_in = {'host': hostname}
        self.headers_out = {}
        self.err_headers_out = {}
        self.error_logged = False

    def log_error(self, msg):
        self.error_logged = True

class WebHandlerTestWithPort(unittest.TestCase):

    def setUp(self):
        self.wh = webhandler.WebHandler()
        self.wh.cfg = FakeConfig('/', 'foo', 'test.local:8080')
        self.wh.req = FakeRequest('foo.test.local:8080', 'GET', '/nowhere')

    def testRedirectHttp(self):
        self.assertRaises(webhandler.HttpMoved, self.wh._redirectHttp,
                '/nowhere')
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local:8080/nowhere')

    def testPermanentRedirect(self):
        self.assertRaises(webhandler.HttpMoved, self.wh._redirect,
                'http://foo.test.local:8080/nowhere')
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local:8080/nowhere')

    def testTemporaryRedirect(self):
        self.assertRaises(webhandler.HttpMovedTemporarily,
                self.wh._redirect, "http://foo.test.local:8080/nowhere",
                {'temporary': False})
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local:8080/nowhere')

    def testBadRedirect(self):
        self.assertRaises(webhandler.HttpMoved,
                self.wh._redirect, "nowhere")
        self.failUnless(self.wh.req.error_logged)


class WebHandlerTestWithoutPort(unittest.TestCase):

    def setUp(self):
        self.wh = webhandler.WebHandler()
        self.wh.cfg = FakeConfig('/', 'foo', 'test.local')
        self.wh.req = FakeRequest('foo.test.local', 'GET', '/nowhere')

    def testRedirectHttpWOP(self):
        self.assertRaises(webhandler.HttpMoved, self.wh._redirectHttp,
                '/nowhere')
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local/nowhere')

    def testPermanentRedirectWOP(self):
        self.assertRaises(webhandler.HttpMoved, self.wh._redirect,
                'http://foo.test.local/nowhere')
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local/nowhere')

    def testTemporaryRedirectWOP(self):
        self.assertRaises(webhandler.HttpMovedTemporarily,
                self.wh._redirect, "http://foo.test.local/nowhere",
                {'temporary': False})
        self.assertEqual(self.wh.req.headers_out['Location'],
                'http://foo.test.local/nowhere')

    def testBadRedirectWOP(self):
        self.assertRaises(webhandler.HttpMoved,
                self.wh._redirect, "nowhere")
        self.failUnless(self.wh.req.error_logged)


if __name__ == "__main__":
    unittest.main()

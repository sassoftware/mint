#!/usr/bin/python
#
# Copyright (c) 2005-2007 rPath, Inc.
#
# All Rights Reserved
#

import unittest

from mint.web import webhandler
from mint_rephelp import FakeRequest

class FakeConfig(object):
    __slots__ = [ 'basePath', 'hostname', ]

    def __init__(self, basepath, hostname, extdomainname):
        self.basePath = basepath
        self.hostname = hostname

class WebHandlerTestWithPort(unittest.TestCase):

    def setUp(self):
        self.wh = webhandler.WebHandler()
        self.wh.cfg = FakeConfig('/', 'foo', 'test.local:8080')
        self.wh.req = FakeRequest('foo.test.local:8080', 'GET', '/nowhere')
        self.wh.baseUrl = 'http://foo.test.local:8080/'

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


class WebHandlerTestWithoutPort(unittest.TestCase):

    def setUp(self):
        self.wh = webhandler.WebHandler()
        self.wh.cfg = FakeConfig('/', 'foo', 'test.local')
        self.wh.req = FakeRequest('foo.test.local', 'GET', '/nowhere')
        self.wh.baseUrl = 'http://foo.test.local/'

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



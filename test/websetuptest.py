#!/usr/bin/python2.4
#
# Copyright (c) 2005-2006 rPath, Inc.
#
# All Rights Reserved
#

import os
import testsuite
import unittest
testsuite.setup()

# define this BEFORE ANYTHING ELSE rbuilder/conary related
from mint import config
config.RBUILDER_CONFIG = '/dev/null'

from mint.web import setup
from mint.web.webhandler import HttpForbidden, HttpNotFound, HttpMoved

from conary import versions
from repostest import testRecipe

import fixtures
import mint_rephelp

class FakeRequest(object):
    __slots__ = [ 'err_headers_out', 'hostname', 'headers_in',
            'headers_out', 'method', 'error_logged', 'content_type']

    def __init__(self, hostname, methodname, filename):
        self.method = methodname
        self.hostname = hostname
        self.headers_in = {'host': hostname}
        self.headers_out = {}
        self.err_headers_out = {}
        self.error_logged = False
        self.content_type = 'text/xhtml'

    def log_error(self, msg):
        self.error_logged = True

class MintTest(mint_rephelp.WebRepositoryHelper):
    def testFirstTimeSetupRedirect(self):
        # this test needs to be re-done
        raise testsuite.SkipTestException
        self.mintCfg.configured = False
        self.resetRepository()

        page = self.assertCode('/', code = 302)
        assert(page.headers['Location'] == '/setup/')

        page = self.assertContent('/setup/', ok_codes = [302],
            content = "Please create a file called")

        sid = self.cookies.items()[0][1]['/']['pysid'].value
        secureFile = self.mintCfg.dataPath + "/" + sid + ".txt"

        f = file(secureFile, 'w')
        f.close()

        page = self.assertContent('/setup/', ok_codes = [200],
            content = "rBuilder Build Setup")

        # set site back to configured
        self.mintCfg.configured = True

class SetupHandlerTest(fixtures.FixturedUnitTest):

    def __system(*args):
        return 0

    def setUp(self):
        self.sh = setup.SetupHandler()
        self.sh.cfg = config.MintConfig()
        self.sh.cfg.hostname = 'foo'
        self.sh.cfg.externalDomainName = 'test.local'
        self.sh.cfg.siteDomainName = 'test.local'
        self.sh.cfg.configured = False
        self.oldsystem = os.system
        os.system = self.__system

    def tearDown(self):
        os.system = self.oldsystem

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetup(self, db, data):
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        func = self.sh.handle(context)
        ret = func(auth)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupBadRequest(self, db, data):
        """ Test failure (hostname is not FQDN) """
        self.sh.req = FakeRequest('foo', 'GET', '/setup')
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        func = self.sh.handle(context)
        ret = func(auth)
        self.failUnless('You must access the rBuilder server as a fully-qualified domain name' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupNonAdmin(self, db, data):
        """ Test failure (user is non-admin) """
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')
        self.sh.cfg.configured = True

        client = self.getClient('user')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': '', 'client': client}
        self.assertRaises(HttpForbidden, self.sh.handle, context)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupBadCommand(self, db, data):
        """ Test failure (bad command given) """
        self.sh.req = FakeRequest('foo.test.local', 'GET', '/setup')

        client = self.getClient('user')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'zxcvb', 'client': client}
        self.assertRaises(HttpNotFound, self.sh.handle, context)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Full")
    def testSetupConfig(self, db, data):
        """ Test configuration generation """
        self.sh.req = FakeRequest('foo.testl.local', 'GET', '/config')
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'config', 'client': client}
        func = self.sh.handle(context)
        ret = func(auth)
        self.failUnless('configured' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupAndRestart(self, db, data):
        """ Test process setup"""
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'new_username': 'fooadmin',
                   'new_email': 'fooadmin@rpath.local',
                   'new_password': 'foopass',
                   'new_password2': 'foopass' }

        self.sh.req = FakeRequest('foo.rpath.local', 'GET', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration Complete</h1>' in ret)

        context = {'auth': auth, 'cmd': 'restart', 'client': client}
        func = self.sh.handle(context)
        self.assertRaises(HttpMoved, func, auth)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupBadPasswords(self, db, data):
        """ Test password mismatch """
        fields = { 'hostName': 'foo',
                   'siteDomainName': 'rpath.local',
                   'new_username': 'fooadmin',
                   'new_email': 'fooadmin@rpath.local',
                   'new_password': 'foopass',
                   'new_password2': 'foopass43' }

        self.sh.req = FakeRequest('foo.rpath.local', 'GET', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)

    @testsuite.context("more_cowbell")
    @fixtures.fixture("Empty")
    def testProcessSetupBlank(self, db, data):
        """ Test password mismatch """
        fields = { 'hostName': '',
                   'siteDomainName': '',
                   'new_username': '',
                   'new_email': '',
                   'new_password': '',
                   'new_password2': '' }

        self.sh.req = FakeRequest('foo.rpath.local', 'GET', '/processSetup')
        self.sh.cfg = self.cfg
        self.sh.cfg.configured = False
        client = self.getClient('admin')
        auth = client.checkAuth()
        context = {'auth': auth, 'cmd': 'processSetup', 'client': client, 'fields': fields}
        func = self.sh.handle(context)
        ret = func(auth = auth, **fields)
        self.failUnless('<h1>rBuilder Configuration</h1>' in ret)


if __name__ == '__main__':
    testsuite.main()

